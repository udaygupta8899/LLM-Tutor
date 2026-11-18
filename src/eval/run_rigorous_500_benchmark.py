import json
import time
from typing import Dict, Any, List
from src.security.prompt_injection_detector import PromptInjectionDetector

def run_benchmark():
    with open("src/eval/benchmark_dataset_500.json", "r") as f:
        all_samples = json.load(f)
        
    malicious = [s for s in all_samples if s["is_malicious"] == 1][:250]
    benign = [s for s in all_samples if s["is_malicious"] == 0][:250]
    dataset = malicious + benign
    
    print(f"=== Starting 500-Sample Rigorous Security Benchmark ===")
    print(f"Total Samples: {len(dataset)} (Malicious: {len(malicious)}, Benign: {len(benign)})\n")
    
    detector = PromptInjectionDetector()
    
    # Naive baseline keywords
    NAIVE_KEYWORDS = [
        "ignore", "disregard", "bypass", "jailbreak", "dan", "developer mode",
        "system prompt", "secret", "override", "root", "unrestricted", "<|im_start|>"
    ]
    
    results_custom = {
        "tp": 0, "fp": 0, "tn": 0, "fn": 0,
        "latencies": [],
        "category_stats": {},
        "false_negatives": [],
        "false_positives": []
    }
    
    results_baseline = {
        "tp": 0, "fp": 0, "tn": 0, "fn": 0
    }
    
    for i, item in enumerate(dataset, start=1):
        text = item["text"]
        is_mal = item["is_malicious"]
        category = item.get("category", "Unspecified")
        is_doc = item.get("is_doc", False)
        
        if category not in results_custom["category_stats"]:
            results_custom["category_stats"][category] = {"total": 0, "correct": 0, "flagged": 0}
        results_custom["category_stats"][category]["total"] += 1
        
        # 1. Custom Detector
        t0 = time.perf_counter()
        insp = detector.inspect(text, is_document=is_doc)
        dt = (time.perf_counter() - t0) * 1000.0  # ms
        results_custom["latencies"].append(dt)
        
        # Predicted malicious if action != ALLOW or risk_score >= 0.25
        pred_mal_custom = 1 if (insp["action"] in ["BLOCK", "QUARANTINE", "WARN", "SANITIZE"] or insp["risk_score"] >= 0.25) else 0
        
        if pred_mal_custom == 1:
            results_custom["category_stats"][category]["flagged"] += 1
            
        if is_mal == 1 and pred_mal_custom == 1:
            results_custom["tp"] += 1
            results_custom["category_stats"][category]["correct"] += 1
        elif is_mal == 0 and pred_mal_custom == 0:
            results_custom["tn"] += 1
            results_custom["category_stats"][category]["correct"] += 1
        elif is_mal == 0 and pred_mal_custom == 1:
            results_custom["fp"] += 1
            results_custom["false_positives"].append({
                "index": i,
                "text": text,
                "category": category,
                "risk_score": insp["risk_score"],
                "action": insp["action"],
                "detected_patterns": insp["detected_patterns"],
                "explanation": insp["explanation"]
            })
        elif is_mal == 1 and pred_mal_custom == 0:
            results_custom["fn"] += 1
            results_custom["false_negatives"].append({
                "index": i,
                "text": text,
                "category": category,
                "risk_score": insp["risk_score"],
                "action": insp["action"],
                "explanation": insp["explanation"]
            })
            
        # 2. Naive Baseline
        lower_text = text.lower()
        pred_mal_base = 1 if any(kw in lower_text for kw in NAIVE_KEYWORDS) else 0
        if is_mal == 1 and pred_mal_base == 1:
            results_baseline["tp"] += 1
        elif is_mal == 0 and pred_mal_base == 0:
            results_baseline["tn"] += 1
        elif is_mal == 0 and pred_mal_base == 1:
            results_baseline["fp"] += 1
        elif is_mal == 1 and pred_mal_base == 0:
            results_baseline["fn"] += 1

    # Metrics calculation
    def calc_metrics(res, total_p, total_n):
        tp, fp, tn, fn = res["tp"], res["fp"], res["tn"], res["fn"]
        acc = (tp + tn) / (tp + tn + fp + fn)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / total_n if total_n > 0 else 0.0
        fnr = fn / total_p if total_p > 0 else 0.0
        return {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "Accuracy": acc, "Precision": prec, "Recall": rec,
            "Specificity": spec, "F1_Score": f1,
            "FPR": fpr, "FNR": fnr
        }

    m_custom = calc_metrics(results_custom, len(malicious), len(benign))
    m_base = calc_metrics(results_baseline, len(malicious), len(benign))
    avg_latency = sum(results_custom["latencies"]) / len(results_custom["latencies"])

    report = {
        "dataset_summary": {
            "total_samples": len(dataset),
            "malicious_samples": len(malicious),
            "benign_samples": len(benign)
        },
        "custom_detector_metrics": m_custom,
        "naive_baseline_metrics": m_base,
        "average_inspection_latency_ms": round(avg_latency, 3),
        "category_breakdown": results_custom["category_stats"],
        "error_analysis": {
            "total_false_positives": len(results_custom["false_positives"]),
            "false_positives_examples": results_custom["false_positives"],
            "total_false_negatives": len(results_custom["false_negatives"]),
            "false_negatives_examples": results_custom["false_negatives"]
        }
    }

    print("=" * 70)
    print("500-SAMPLE RIGOROUS BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Metric':<25} | {'Custom Detector':<18} | {'Naive Baseline':<18}")
    print("-" * 70)
    for k in ["Accuracy", "Precision", "Recall", "Specificity", "F1_Score", "FPR", "FNR"]:
        v_c = f"{m_custom[k]*100:.2f}%"
        v_b = f"{m_base[k]*100:.2f}%"
        print(f"{k:<25} | {v_c:<18} | {v_b:<18}")
    print("-" * 70)
    print(f"{'True Positives (TP)':<25} | {m_custom['TP']:<18} | {m_base['TP']:<18}")
    print(f"{'False Positives (FP)':<25} | {m_custom['FP']:<18} | {m_base['FP']:<18}")
    print(f"{'True Negatives (TN)':<25} | {m_custom['TN']:<18} | {m_base['TN']:<18}")
    print(f"{'False Negatives (FN)':<25} | {m_custom['FN']:<18} | {m_base['FN']:<18}")
    print(f"{'Mean Latency':<25} | {avg_latency:.3f} ms           | <0.01 ms")
    print("=" * 70)
    print(f"\nCategory Breakdown (Custom Detector):")
    for cat, stat in results_custom["category_stats"].items():
        acc = (stat["correct"] / stat["total"]) * 100
        print(f" - {cat:<32}: {stat['correct']}/{stat['total']} ({acc:.1f}%)")

    print(f"\nDetailed Error Analysis:")
    print(f"False Positives count: {len(results_custom['false_positives'])}")
    for fp in results_custom["false_positives"][:3]:
        print(f"  * [FP] \"{fp['text']}\" -> Flagged as {fp['action']} ({fp['detected_patterns']})")
    print(f"False Negatives count: {len(results_custom['false_negatives'])}")
    for fn in results_custom["false_negatives"][:5]:
        print(f"  * [FN] \"{fn['text']}\" -> Risk Score: {fn['risk_score']} ({fn['category']})")

    with open("large_scale_security_benchmark_500_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved full report to large_scale_security_benchmark_500_report.json")

if __name__ == "__main__":
    run_benchmark()
