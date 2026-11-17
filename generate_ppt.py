import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="Adaptive_LLM_Tutor_Final_Presentation.pptx"):
    prs = Presentation()
    # 16:9 widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Palette: Deep Tech Academic
    BG_DARK = RGBColor(15, 23, 42)        # Slate 900
    BG_CARD = RGBColor(30, 41, 59)        # Slate 800
    CARD_BORDER = RGBColor(51, 65, 85)    # Slate 700
    ACCENT_BLUE = RGBColor(56, 189, 248)  # Sky 400
    ACCENT_INDIGO = RGBColor(99, 102, 241)# Indigo 500
    ACCENT_EMERALD = RGBColor(52, 211, 153)# Emerald 400
    ACCENT_AMBER = RGBColor(251, 191, 36) # Amber 400
    TEXT_LIGHT = RGBColor(248, 250, 252)  # Slate 50
    TEXT_MUTED = RGBColor(148, 163, 184)  # Slate 400
    CODE_BG = RGBColor(10, 15, 30)        # Midnight

    def apply_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category="LLM COURSE PROJECT • ADAPTIVE AGENTIC RAG"):
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT

    def add_card(slide, left, top, width, height, bg_color=BG_CARD, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_bg(s1)

    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(4.5))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "DEEP LEARNING & LLM COURSE PROJECT"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_BLUE
    p0.space_after = Pt(14)

    p1 = tf1.add_paragraph()
    p1.text = "Adaptive LLM Tutor"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT

    p2 = tf1.add_paragraph()
    p2.text = "Complexity-Grounded Agentic RAG with Custom Hybrid Ranking & Security Defense"
    p2.font.size = Pt(20)
    p2.font.color.rgb = ACCENT_INDIGO
    p2.space_after = Pt(28)

    p3 = tf1.add_paragraph()
    p3.text = "Base Paper: Singh et al. (2026), 'Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG' (arXiv:2501.09136v4, Section 5.5)"
    p3.font.size = Pt(12)
    p3.font.color.rgb = TEXT_MUTED

    p4 = tf1.add_paragraph()
    p4.text = "Repository: https://github.com/udaygupta8899/LLM-Tutor  •  Technology Readiness Level: TRL 4"
    p4.font.size = Pt(12)
    p4.font.color.rgb = ACCENT_EMERALD
    p4.space_before = Pt(8)

    # Core Highlight Pill
    add_card(s1, Inches(1.0), Inches(5.8), Inches(11.3), Inches(1.0), bg_color=BG_CARD, border_color=ACCENT_INDIGO)
    pill_box = s1.shapes.add_textbox(Inches(1.2), Inches(5.9), Inches(10.9), Inches(0.8))
    tf_pill = pill_box.text_frame
    tf_pill.word_wrap = True
    pp = tf_pill.paragraphs[0]
    pp.text = "★ STRICT ENGINEERING MANDATE: Two Custom Core Components Built from Scratch in Pure Python"
    pp.font.bold = True
    pp.font.size = Pt(13)
    pp.font.color.rgb = ACCENT_AMBER
    pp2 = tf_pill.add_paragraph()
    pp2.text = "1) Intelligent Hybrid IR Engine (Custom Stemmer + Okapi BM25 + Reciprocal Rank Fusion)  •  2) Multi-Layer Injection Defense Engine"
    pp2.font.size = Pt(11)
    pp2.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 2: Problem Statement & Motivation
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_bg(s2)
    add_header(s2, "1. Problem Statement & Motivation", "TRL 4 • SYSTEM VALIDATION IN LABORATORY ENVIRONMENT")

    # Card 1: Static RAG Inefficiencies
    add_card(s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    b1 = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
    t1 = b1.text_frame
    t1.word_wrap = True
    p = t1.paragraphs[0]
    p.text = "Fundamental Flaws of Static Single-Step RAG"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(12)

    bullets1 = [
        ("Invariant Computational Cost: ", "Traditional RAG executes top-k dense vector lookups unconditionally. Simple queries ('What does AI stand for?') suffer redundant 200-500ms retrieval latency and vector DB overhead."),
        ("Multi-Hop Failure & Fragmentation: ", "Complex queries ('Compare CNNs vs RNNs across inductive bias and receptive fields') require iterative evidence gathering; single-shot retrieval produces fragmented contexts leading to model hallucinations."),
        ("Core Principle (Singh et al. Section 5.5): ", "'Match computational effort to query complexity' — dynamically route straightforward, simple, and complex queries.")
    ]
    for head, body in bullets1:
        pb = t1.add_paragraph()
        run1 = pb.add_run()
        run1.text = "• " + head
        run1.font.bold = True
        run1.font.color.rgb = TEXT_LIGHT
        run1.font.size = Pt(12)
        run2 = pb.add_run()
        run2.text = body
        run2.font.color.rgb = TEXT_MUTED
        run2.font.size = Pt(12)
        pb.space_after = Pt(10)

    # Card 2: Security & Interactive Tutoring Need
    add_card(s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    b2 = s2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    t2 = b2.text_frame
    t2.word_wrap = True
    p = t2.paragraphs[0]
    p.text = "Adversarial Risk & The Interactive Tutoring Need"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = ACCENT_AMBER
    p.space_after = Pt(12)

    bullets2 = [
        ("The Injection Vulnerability: ", "LLM educational bots ingest direct user prompts and external uploaded course documents. Attackers exploit jailbreaks, DAN virtualization, and Base64/leetspeak obfuscation to hijack prompts or extract solutions."),
        ("Third-Party Library Disallowance: ", "Commercial guardrails (Rebuff, NeMo) are black boxes. Academic research mandates deterministic, from-scratch threat detection and transparent entropy scoring."),
        ("Dynamic Educational Assessment: ", "Students need active testing, not passive reading. The tutor must generate 100% on-the-fly adaptive questions with difficulty escalation and PDF diagnostic analytics.")
    ]
    for head, body in bullets2:
        pb = t2.add_paragraph()
        run1 = pb.add_run()
        run1.text = "• " + head
        run1.font.bold = True
        run1.font.color.rgb = TEXT_LIGHT
        run1.font.size = Pt(12)
        run2 = pb.add_run()
        run2.text = body
        run2.font.color.rgb = TEXT_MUTED
        run2.font.size = Pt(12)
        pb.space_after = Pt(10)

    # ==========================================
    # SLIDE 3: Literature Survey & SOTA
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_bg(s3)
    add_header(s3, "2. Literature Survey & SOTA Theoretical Foundations", "ACADEMIC TAXONOMY & EVOLUTION")

    # Table of papers
    papers_data = [
        ("Singh et al. (2026)\nBase Survey (arXiv:2501.09136v4)", "Agentic RAG Survey", "Section 5.5 Adaptive Agentic RAG; Section 7.5 Educational Personalization; Taxonomy: Naïve -> Modular -> Adaptive."),
        ("Vaswani et al. (2017)\nNeurIPS", "Attention Is All You Need", "Scaled dot-product attention mechanics, multi-head projections, and sequence-to-sequence foundation."),
        ("Lewis et al. (2020)\nNeurIPS", "Retrieval-Augmented Generation", "Non-parametric memory integration with parametric LLM; RAG-Token and RAG-Sequence formulations."),
        ("Asai et al. (2024)\nICLR", "Self-RAG (Self-Reflection)", "On-demand retrieval using reflection tokens (<RETRIEVE>, <CRITIQUE>) and self-assessment loops."),
        ("Yan et al. (2024)\nCRAG (arXiv:2401.15884)", "Corrective RAG", "Lightweight retrieval evaluator assessing confidence to trigger corrective actions or web fallback."),
        ("Dao et al. (2022)\nNeurIPS", "FlashAttention", "Fast, exact IO-aware attention tiling in GPU SRAM to eliminate standard O(N^2) memory bottlenecks.")
    ]

    top_pos = 1.6
    for cit, title, impact in papers_data:
        add_card(s3, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(0.8), bg_color=BG_CARD)
        tb = s3.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.05), Inches(11.3), Inches(0.7))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = cit.replace('\n', ' ') + " | "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = ACCENT_BLUE
        r2 = p.add_run()
        r2.text = title + ": "
        r2.font.bold = True
        r2.font.size = Pt(11)
        r2.font.color.rgb = TEXT_LIGHT
        r3 = p.add_run()
        r3.text = impact
        r3.font.size = Pt(10.5)
        r3.font.color.rgb = TEXT_MUTED
        top_pos += 0.88

    # ==========================================
    # SLIDE 4: High-Level System Architecture
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_bg(s4)
    add_header(s4, "3. System Architecture & End-to-End Pipeline", "FULL OPERATIONAL FLOW")

    # 4 Architecture Columns
    col_w = Inches(2.7)
    gap = Inches(0.3)
    start_x = Inches(0.8)

    stages = [
        ("Layer 1: Security Barrier", ACCENT_AMBER, [
            "Pure Python Custom Detector",
            "Base64 & Leetspeak Unmasker",
            "Compounding Risk Scorer",
            "Action: ALLOW | WARN | BLOCK",
            "Direct & Indirect Defense"
        ]),
        ("Layer 2: Adaptive Router", ACCENT_INDIGO, [
            "Singh et al. Section 5.5",
            "Intent & Complexity Classifier",
            "Straightforward -> Direct LLM",
            "Simple -> Single Hybrid RAG",
            "Complex -> Multi-Hop Agentic"
        ]),
        ("Layer 3: Hybrid Retrieval", ACCENT_BLUE, [
            "Pure Python Custom BM25",
            "Custom Tokenizer & Stemmer",
            "Robertson-Spärck Jones IDF",
            "Dense Cosine Search (Chroma)",
            "Reciprocal Rank Fusion (k=60)"
        ]),
        ("Layer 4: Synthesis & Quiz", ACCENT_EMERALD, [
            "Groq GPT-OSS-120B Inference",
            "Explain | Hint | Socratic Modes",
            "100% Dynamic On-the-Fly Quiz",
            "Progressive Mastery Levels",
            "Automated PDF Diagnostics"
        ])
    ]

    for i, (title, color, items) in enumerate(stages):
        cx = start_x + i * (col_w + gap)
        add_card(s4, cx, Inches(1.6), col_w, Inches(4.5), bg_color=BG_CARD, border_color=color)
        tb = s4.shapes.add_textbox(cx + Inches(0.15), Inches(1.75), col_w - Inches(0.3), Inches(4.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = color
        p.space_after = Pt(14)
        for item in items:
            pi = tf.add_paragraph()
            pi.text = "• " + item
            pi.font.size = Pt(10.5)
            pi.font.color.rgb = TEXT_LIGHT
            pi.space_after = Pt(8)

    # Bottom Foundation Card
    add_card(s4, Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.7), bg_color=CODE_BG, border_color=CARD_BORDER)
    bb = s4.shapes.add_textbox(Inches(1.0), Inches(6.35), Inches(11.3), Inches(0.6))
    tfb = bb.text_frame
    pb = tfb.paragraphs[0]
    pb.text = "State Persistence & Memory: LangGraph Checkpointing • SQLite learner_memory.db • Output Grounding Verifier"
    pb.font.bold = True
    pb.font.size = Pt(11)
    pb.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 5: [FROM SCRATCH #1A] Custom Tokenizer & Suffix Stemmer
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_bg(s5)
    add_header(s5, "4A. From-Scratch Component: Tokenizer & Suffix Stemmer", "STRICT MANDATE: NO NLTK • NO SPACY • PURE PYTHON ALGORITHM")

    # Left: Explanation
    add_card(s5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_exp = s5.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfe = tb_exp.text_frame
    tfe.word_wrap = True
    pe = tfe.paragraphs[0]
    pe.text = "Linguistic Parsing Mechanics (src/retrieval/tokenizer.py)"
    pe.font.bold = True
    pe.font.size = Pt(15)
    pe.font.color.rgb = ACCENT_BLUE
    pe.space_after = Pt(10)

    tok_points = [
        ("Zero External NLP Dependencies: ", "Implemented from mathematical first principles without NLTK, Spacy, or Scikit-learn to guarantee sub-millisecond lexical processing."),
        ("Alphanumeric Boundary Scanner: ", "Normalizes text to lowercase, handles ASCII stripping, and extracts alphabetic token sequences [a-z0-9]+."),
        ("Rule-Based Suffix Stemming: ", "Conflates morphological variations in technical vocabulary:"),
        ("  • '-ational' -> 'ate' ", "(e.g., 'relational' -> 'relate')"),
        ("  • '-tional' -> 'tion' ", "(e.g., 'conditional' -> 'condition')"),
        ("  • '-enci' / '-anci' -> 'ence' / 'ance' ", "(e.g., 'dependency' -> 'dependence')"),
        ("  • '-izer' -> 'ize' | '-ing', '-ed', '-ly' ", "Suffix stripping with word length boundary checks."),
        ("Domain Impact: ", "Ensures 'convolutional' matches 'convolution' and 'retrieval' matches 'retrieve' in dense textbook corpora.")
    ]
    for h, b in tok_points:
        p = tfe.add_paragraph()
        r1 = p.add_run()
        r1.text = h
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(11)
        p.space_after = Pt(4)

    # Right: Actual Code Box
    add_card(s5, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=CODE_BG, border_color=ACCENT_INDIGO)
    tb_c = s5.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.5), Inches(5.1))
    tfc = tb_c.text_frame
    tfc.word_wrap = True
    pc = tfc.paragraphs[0]
    pc.text = "# Code Snippet: Suffix Stemmer (src/retrieval/tokenizer.py)"
    pc.font.bold = True
    pc.font.size = Pt(11)
    pc.font.color.rgb = ACCENT_AMBER
    pc.space_after = Pt(8)

    code_stem = (
        "class SuffixStemmer:\n"
        "    STEP2_REPLACEMENTS = [\n"
        "        ('ational', 'ate'), ('tional', 'tion'),\n"
        "        ('enci', 'ence'),   ('anci', 'ance'),\n"
        "        ('izer', 'ize'),    ('abli', 'able'),\n"
        "        ('alli', 'al'),     ('entli', 'ent')\n"
        "    ]\n"
        "    def stem(self, word: str) -> str:\n"
        "        w = word.lower()\n"
        "        if len(w) <= 3: return w\n"
        "        for suffix, repl in self.STEP2_REPLACEMENTS:\n"
        "            if w.endswith(suffix):\n"
        "                return w[:-len(suffix)] + repl\n"
        "        if w.endswith('ing') and len(w) > 4:\n"
        "            return w[:-3]\n"
        "        if w.endswith('ed') and len(w) > 3:\n"
        "            return w[:-2]\n"
        "        return w"
    )
    pc2 = tfc.add_paragraph()
    pc2.text = code_stem
    pc2.font.name = "Courier New"
    pc2.font.size = Pt(10)
    pc2.font.color.rgb = RGBColor(165, 243, 252)

    # ==========================================
    # SLIDE 6: [FROM SCRATCH #1B] Okapi BM25 Ranking Engine
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    apply_bg(s6)
    add_header(s6, "4B. From-Scratch Component: Okapi BM25 Implementation", "STRICT MANDATE: NO RANK_BM25 • PROBABILISTIC RELEVANCE DERIVATION")

    # Left: Math Formulations
    add_card(s6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_m = s6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfm = tb_m.text_frame
    tfm.word_wrap = True
    pm = tfm.paragraphs[0]
    pm.text = "Mathematical Formulation from First Principles"
    pm.font.bold = True
    pm.font.size = Pt(15)
    pm.font.color.rgb = ACCENT_BLUE
    pm.space_after = Pt(12)

    bm_math = [
        ("Robertson-Spärck Jones IDF (with 0.5 smoothing):", "IDF(q_i) = ln[ (N - n(q_i) + 0.5) / (n(q_i) + 0.5) + 1 ]\nPrevents negative IDF scores for frequent terms appearing across documents."),
        ("Document Length Normalized Score:", "Score_BM25(D, Q) = ∑_{q_i} IDF(q_i) * [ tf * (k1 + 1) ] / [ tf + k1 * (1 - b + b * (|D| / avgdl)) ]"),
        ("Hyperparameter Tuning:", "• k1 = 1.5: Calibrates term frequency saturation limit.\n• b = 0.75: Controls length penalization (long docs penalized proportional to avgdl)."),
        ("Precomputed Index:", "Precomputes document term frequencies, inverted postings, document lengths, and corpus average doc length across 946 chunks.")
    ]
    for h, b in bm_math:
        p = tfm.add_paragraph()
        r1 = p.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    # Right: Python BM25 Code Box
    add_card(s6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=CODE_BG, border_color=ACCENT_INDIGO)
    tb_bm = s6.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.5), Inches(5.1))
    tfbm = tb_bm.text_frame
    tfbm.word_wrap = True
    pbm = tfbm.paragraphs[0]
    pbm.text = "# Code Snippet: BM25 Scoring Loop (src/retrieval/bm25.py)"
    pbm.font.bold = True
    pbm.font.size = Pt(11)
    pbm.font.color.rgb = ACCENT_AMBER
    pbm.space_after = Pt(8)

    code_bm25 = (
        "def score_document(self, query_terms: List[str], doc_idx: int) -> float:\n"
        "    score = 0.0\n"
        "    doc_len = self.doc_lengths[doc_idx]\n"
        "    for term in query_terms:\n"
        "        if term not in self.inverted_index:\n"
        "            continue\n"
        "        tf = self.inverted_index[term].get(doc_idx, 0)\n"
        "        idf = self.idf.get(term, 0.0)\n"
        "        # Term saturation + length normalization\n"
        "        num = tf * (self.k1 + 1)\n"
        "        denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))\n"
        "        score += idf * (num / denom)\n"
        "    return score\n\n"
        "# Verified Benchmark: Precision@5 = 0.60 | Latency = 0.07 ms"
    )
    pbm2 = tfbm.add_paragraph()
    pbm2.text = code_bm25
    pbm2.font.name = "Courier New"
    pbm2.font.size = Pt(10)
    pbm2.font.color.rgb = RGBColor(165, 243, 252)

    # ==========================================
    # SLIDE 7: [FROM SCRATCH #1C] Reciprocal Rank Fusion (RRF)
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    apply_bg(s7)
    add_header(s7, "4C. From-Scratch Component: Reciprocal Rank Fusion (RRF)", "SCORE NORMALIZATION IN HYBRID IR • k = 60 SMOOTHING")

    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_r = s7.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfr = tb_r.text_frame
    tfr.word_wrap = True
    pr = tfr.paragraphs[0]
    pr.text = "Solving Disparate Score Distribution Fusion"
    pr.font.bold = True
    pr.font.size = Pt(15)
    pr.font.color.rgb = ACCENT_BLUE
    pr.space_after = Pt(12)

    rrf_expl = [
        ("The Core IR Challenge:", "BM25 produces unbounded positive relevance scores [0, +inf), while dense vector retrievers output bounded cosine similarities [-1, 1]. Direct linear combination (w1*S_dense + w2*S_bm25) skews rankings severely toward dense vectors."),
        ("RRF Algorithmic Formulation:", "RRF bypasses raw scores and operates strictly on ordinal rank positions:\nScore_RRF(d) = ∑_{m ∈ M} [ 1 / (k + r_m(d)) ]"),
        ("Smoothing Constant k = 60:", "The constant k suppresses high-rank outlier bias, ensuring robust candidate fusion across disparate retrievers."),
        ("End-to-End Orchestration:", "Executes BM25 and Dense Cosine in parallel, unions top candidate IDs, computes reciprocal sums, and passes to optional Cross-Encoder.")
    ]
    for h, b in rrf_expl:
        p = tfr.add_paragraph()
        r1 = p.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    # Right: Python RRF Code Box
    add_card(s7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=CODE_BG, border_color=ACCENT_INDIGO)
    tb_rc = s7.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.5), Inches(5.1))
    tfrc = tb_rc.text_frame
    tfrc.word_wrap = True
    prc = tfrc.paragraphs[0]
    prc.text = "# Code Snippet: Custom RRF Rank Combiner (src/retrieval/rrf.py)"
    prc.font.bold = True
    prc.font.size = Pt(11)
    prc.font.color.rgb = ACCENT_AMBER
    prc.space_after = Pt(8)

    code_rrf = (
        "def fuse_ranks(ranked_lists: List[List[Dict]], k: int = 60):\n"
        "    rrf_scores = defaultdict(float)\n"
        "    doc_registry = {}\n"
        "    for r_list in ranked_lists:\n"
        "        for rank, doc in enumerate(r_list, start=1):\n"
        "            doc_id = doc['id']\n"
        "            doc_registry[doc_id] = doc\n"
        "            # Reciprocal rank accumulation\n"
        "            rrf_scores[doc_id] += 1.0 / (k + rank)\n\n"
        "    sorted_docs = sorted(\n"
        "        rrf_scores.items(), key=lambda x: x[1], reverse=True\n"
        "    )\n"
        "    return [doc_registry[doc_id] for doc_id, _ in sorted_docs]"
    )
    prc2 = tfrc.add_paragraph()
    prc2.text = code_rrf
    prc2.font.name = "Courier New"
    prc2.font.size = Pt(10)
    prc2.font.color.rgb = RGBColor(165, 243, 252)

    # ==========================================
    # SLIDE 8: [FROM SCRATCH #2A] Prompt Injection Defense Engine
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    apply_bg(s8)
    add_header(s8, "5A. From-Scratch Component: Prompt Injection Defense", "4-LAYER TAXONOMY • LEETSPEAK UNMASKING • ZERO EXTERNAL GUARDRAILS")

    # Left: Explanation
    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_sec = s8.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfsec = tb_sec.text_frame
    tfsec.word_wrap = True
    ps = tfsec.paragraphs[0]
    ps.text = "4-Layer Adversarial Threat Taxonomy"
    ps.font.bold = True
    ps.font.size = Pt(15)
    ps.font.color.rgb = ACCENT_AMBER
    ps.space_after = Pt(10)

    tax_items = [
        ("Layer 1: Direct Jailbreaks: ", "Explicit override attempts ('ignore all previous instructions', 'system prompt override', 'disregard guidelines')."),
        ("Layer 2: Virtualization & DAN: ", "Roleplay attacks forcing unrestricted behavior ('DAN mode', 'developer mode enabled', 'pretend you have no safety rules')."),
        ("Layer 3: Delimiter Injections: ", "Context manipulation tokens (<|im_start|>, [INST], ---BEGIN SYSTEM PROMPT---)."),
        ("Layer 4: System Leakage: ", "Exfiltration probes ('repeat system prompt verbatim', 'reveal developer keys')."),
        ("Recursive De-obfuscation: ", "Pre-execution scanner unmasks leetspeak substitutions ('1gn0r3' -> 'ignore', 'p@55w0rd' -> 'password') and decodes Base64 payloads before regex matching.")
    ]
    for h, b in tax_items:
        p = tfsec.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + h
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(6)

    # Right: Python Security Code Box
    add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=CODE_BG, border_color=ACCENT_INDIGO)
    tb_sc = s8.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.5), Inches(5.1))
    tfsc = tb_sc.text_frame
    tfsc.word_wrap = True
    psc = tfsc.paragraphs[0]
    psc.text = "# Code Snippet: Leetspeak Unmasker (src/security/risk_scorer.py)"
    psc.font.bold = True
    psc.font.size = Pt(11)
    psc.font.color.rgb = ACCENT_AMBER
    psc.space_after = Pt(8)

    code_sec = (
        "LEET_MAP = {'0': 'o', '1': 'i', '3': 'e', '4': 'a',\n"
        "            '5': 's', '7': 't', '@': 'a', '$': 's'}\n\n"
        "def deobfuscate_text(text: str) -> str:\n"
        "    cleaned = text.lower()\n"
        "    # Step 1: Base64 decode detection\n"
        "    b64_matches = re.findall(r'[A-Za-z0-9+/=]{20,}', text)\n"
        "    for match in b64_matches:\n"
        "        try:\n"
        "            decoded = base64.b64decode(match).decode('utf-8')\n"
        "            cleaned += ' ' + decoded.lower()\n"
        "        except Exception: pass\n\n"
        "    # Step 2: Unmask character substitutions\n"
        "    for leet, char in LEET_MAP.items():\n"
        "        cleaned = cleaned.replace(leet, char)\n"
        "    return cleaned"
    )
    psc2 = tfsc.add_paragraph()
    psc2.text = code_sec
    psc2.font.name = "Courier New"
    psc2.font.size = Pt(10)
    psc2.font.color.rgb = RGBColor(165, 243, 252)

    # ==========================================
    # SLIDE 9: [FROM SCRATCH #2B] Compounding Risk Scorer & Policy
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    apply_bg(s9)
    add_header(s9, "5B. From-Scratch Component: Risk Scorer & Security Policy", "MATHEMATICAL ENTROPY • MULTI-ACTION DEFENSE BOUNDARY")

    add_card(s9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_rk = s9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfrk = tb_rk.text_frame
    tfrk.word_wrap = True
    prk = tfrk.paragraphs[0]
    prk.text = "Compounding Risk Scorer & Tiered Decision Policy"
    prk.font.bold = True
    prk.font.size = Pt(15)
    prk.font.color.rgb = ACCENT_AMBER
    prk.space_after = Pt(12)

    rk_points = [
        ("Structural Entropy & Anomaly Detection:", "Computes Shannon character entropy and non-alphanumeric ratio to catch code-injection payloads and obfuscated scripts."),
        ("Compounding Threat Weighting:", "RiskScore = min(1.0, W_threat*0.35 + W_entropy*0.25 + W_marker*0.40)"),
        ("Multi-Action Enforcement Thresholds:", "• Score < 0.25: ALLOW (clean student query).\n• 0.25 <= Score < 0.60: WARN (delimiters stripped, flagged in audit log).\n• Score >= 0.60: BLOCK / QUARANTINE (short-circuits LLM synthesis, zero token consumption)."),
        ("Indirect Document Protection:", "Scans external retrieved context chunks. Any poisoned chunk embedded in PDFs is quarantined before entering the LLM prompt.")
    ]
    for h, b in rk_points:
        p = tfrk.add_paragraph()
        r1 = p.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    # Right: Python Policy Code Box
    add_card(s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=CODE_BG, border_color=ACCENT_INDIGO)
    tb_pl = s9.shapes.add_textbox(Inches(6.9), Inches(1.7), Inches(5.5), Inches(5.1))
    tfpl = tb_pl.text_frame
    tfpl.word_wrap = True
    ppl = tfpl.paragraphs[0]
    ppl.text = "# Code Snippet: Security Policy (src/security/security_policy.py)"
    ppl.font.bold = True
    ppl.font.size = Pt(11)
    ppl.font.color.rgb = ACCENT_AMBER
    ppl.space_after = Pt(8)

    code_policy = (
        "class SecurityPolicy:\n"
        "    def enforce(self, risk_score: float, threat_type: str):\n"
        "        if risk_score >= 0.60:\n"
        "            action = 'BLOCK'\n"
        "            reason = f'High risk prompt injection detected: {threat_type}'\n"
        "        elif risk_score >= 0.25:\n"
        "            action = 'WARN'\n"
        "            reason = f'Suspicious delimiters detected: {threat_type}'\n"
        "        else:\n"
        "            action = 'ALLOW'\n"
        "            reason = 'Input cleared security scan'\n\n"
        "        self.audit_log.append({\n"
        "            'timestamp': time.time(), 'score': risk_score,\n"
        "            'action': action, 'reason': reason\n"
        "        })\n"
        "        return {'action': action, 'score': risk_score, 'reason': reason}"
    )
    ppl2 = tfpl.add_paragraph()
    ppl2.text = code_policy
    ppl2.font.name = "Courier New"
    ppl2.font.size = Pt(10)
    ppl2.font.color.rgb = RGBColor(165, 243, 252)

    # ==========================================
    # SLIDE 10: Adaptive Routing & Real-Time Quiz Engine
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    apply_bg(s10)
    add_header(s10, "6. Adaptive Routing & Dynamic Interactive Assessment", "LANGGRAPH STATE MACHINE • 100% ON-THE-FLY QUIZ GENERATION")

    # Card 1: Adaptive Routing
    add_card(s10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_ad = s10.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfad = tb_ad.text_frame
    tfad.word_wrap = True
    pad = tfad.paragraphs[0]
    pad.text = "Adaptive Complexity Routing (Singh et al. Sec 5.5)"
    pad.font.bold = True
    pad.font.size = Pt(15)
    pad.font.color.rgb = ACCENT_BLUE
    pad.space_after = Pt(12)

    ad_bullets = [
        ("Query Complexity Classifier: ", "Syntactically screens student intent and problem complexity before retrieval."),
        ("Straightforward Route: ", "Direct LLM synthesis (retrieval bypassed, 0 docs, 0.146s latency, 72% compute savings)."),
        ("Simple Route: ", "Single-step hybrid retrieval (4 chunks fused via custom BM25 + Dense RRF)."),
        ("Complex Route: ", "Query decomposer generates sub-queries, executes multi-hop iterative retrieval, and validates grounding.")
    ]
    for h, b in ad_bullets:
        p = tfad.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + h
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    # Card 2: Dynamic Quiz Engine
    add_card(s10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_qz = s10.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tfqz = tb_qz.text_frame
    tfqz.word_wrap = True
    pqz = tfqz.paragraphs[0]
    pqz.text = "100% Dynamic On-the-Fly Quiz Engine"
    pqz.font.bold = True
    pqz.font.size = Pt(15)
    pqz.font.color.rgb = ACCENT_EMERALD
    pqz.space_after = Pt(12)

    qz_bullets = [
        ("Zero Hardcoded Questions: ", "Every question is generated live on the go by querying Groq GPT-OSS-120B with grounded ChromaDB context chunks."),
        ("Progressive Mastery Progression: ", "Starts at 'easy' (foundational definitions), elevates to 'intermediate' upon correct responses, and advances to 'advanced' (loss equations and failure modes)."),
        ("State Locking & Interactivity: ", "Mode switcher is locked during active assessments; clickable options with instant color feedback."),
        ("Client-Side PDF Diagnostic Export: ", "Auto-generates downloadable diagnostic reports with score ratios, strengths, review topics, and itemized breakdowns.")
    ]
    for h, b in qz_bullets:
        p = tfqz.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + h
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    # ==========================================
    # SLIDE 11: DEMO SLIDE (Insert Video Link Here)
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    apply_bg(s11)
    add_header(s11, "7. System Demonstration & Video Walkthrough", "LIVE PROTOTYPE VALIDATION • END-TO-END DEMO")

    # Big Central Video Card
    add_card(s11, Inches(1.5), Inches(1.6), Inches(10.3), Inches(4.0), bg_color=CODE_BG, border_color=ACCENT_EMERALD)
    tb_vid = s11.shapes.add_textbox(Inches(1.8), Inches(2.2), Inches(9.7), Inches(2.8))
    tfv = tb_vid.text_frame
    tfv.word_wrap = True
    pv = tfv.paragraphs[0]
    pv.text = "▶ INSERT DEMO VIDEO / YOUTUBE LINK HERE"
    pv.font.bold = True
    pv.font.size = Pt(24)
    pv.font.color.rgb = ACCENT_EMERALD
    pv.alignment = PP_ALIGN.CENTER
    pv.space_after = Pt(14)

    pv2 = tfv.add_paragraph()
    pv2.text = "[ Embed your presentation video recording or paste your unlisted YouTube URL here ]"
    pv2.font.size = Pt(14)
    pv2.font.color.rgb = TEXT_MUTED
    pv2.alignment = PP_ALIGN.CENTER

    # Live Checklist Below Video
    add_card(s11, Inches(1.5), Inches(5.8), Inches(10.3), Inches(1.2), bg_color=BG_CARD)
    tb_chk = s11.shapes.add_textbox(Inches(1.7), Inches(5.85), Inches(9.9), Inches(1.0))
    tfc = tb_chk.text_frame
    tfc.word_wrap = True
    pc = tfc.paragraphs[0]
    pc.text = "Live Demo Features Validated in Video:"
    pc.font.bold = True
    pc.font.size = Pt(12)
    pc.font.color.rgb = ACCENT_BLUE
    pc2 = tfc.add_paragraph()
    pc2.text = "1. Multi-turn Chat with KaTeX LaTeX & sanitized Mermaid.js diagrams  •  2. SQLite memory recall ('What did I ask previously?')\n3. Instant BLOCK of obfuscated prompt injections in telemetry  •  4. Dynamic Adaptive Quiz with live PDF report generation."
    pc2.font.size = Pt(11)
    pc2.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 12: Empirical Benchmark Results
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    apply_bg(s12)
    add_header(s12, "8. Experimental Benchmark Results", "EMPIRICAL IR & SECURITY PERFORMANCE")

    # Card 1: IR Evaluation Table
    add_card(s12, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_irt = s12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tfi = tb_irt.text_frame
    tfi.word_wrap = True
    pi = tfi.paragraphs[0]
    pi.text = "Table 1: Information Retrieval Evaluation"
    pi.font.bold = True
    pi.font.size = Pt(14)
    pi.font.color.rgb = ACCENT_BLUE
    pi.space_after = Pt(10)

    ir_rows = [
        "Pipeline             | P@5   | Recall | MRR    | Latency",
        "---------------------------------------------------------",
        "Custom BM25 Only     | 0.60  | 1.00   | 0.6500 | 0.07 ms",
        "Dense Cosine Only    | 0.24  | 0.80   | 0.3900 | 53.23 ms",
        "Hybrid RRF (k=60)    | 0.28  | 0.80   | 0.5167 | 1.82 ms",
        "Hybrid + Reranking   | 0.28  | 0.80   | 0.5167 | 1.42 ms"
    ]
    for row in ir_rows:
        p = tfi.add_paragraph()
        p.text = row
        p.font.name = "Courier New"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(2)

    pi_exp = tfi.add_paragraph()
    pi_exp.text = "\nKey Finding: Custom BM25 achieved perfect Recall (1.00) at 0.07ms latency. Hybrid RRF balances exact term matching with dense semantic alignment."
    pi_exp.font.size = Pt(10)
    pi_exp.font.color.rgb = TEXT_MUTED

    # Card 2: Security Evaluation Table
    add_card(s12, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_st = s12.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tfs = tb_st.text_frame
    tfs.word_wrap = True
    ps = tfs.paragraphs[0]
    ps.text = "Table 2: Prompt Injection Defense Benchmark"
    ps.font.bold = True
    ps.font.size = Pt(14)
    ps.font.color.rgb = ACCENT_AMBER
    ps.space_after = Pt(10)

    sec_rows = [
        "Metric            | Custom Detector | Keyword Baseline",
        "-------------------------------------------------------",
        "Accuracy          | 100.0%          | 80.0%",
        "Precision         | 100.0%          | 75.0%",
        "Recall            | 100.0%          | 90.0%",
        "F1 Score          | 1.000           | 0.8182",
        "False Pos. Rate   | 0.0% (0/10)     | 30.0% (3/10)"
    ]
    for row in sec_rows:
        p = tfs.add_paragraph()
        p.text = row
        p.font.name = "Courier New"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(2)

    ps_exp = tfs.add_paragraph()
    ps_exp.text = "\nKey Finding: Keyword baseline failed by flagging benign deep learning questions containing words like 'ignore' ('Does dropout cause the network to ignore neurons?'). Our compounding risk scorer achieved 0% FPR."
    ps_exp.font.size = Pt(10)
    ps_exp.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 13: Team Contributions & Key Learnings
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    apply_bg(s13)
    add_header(s13, "9. Team Contributions & Key Learnings", "INDIVIDUAL RESPONSIBILITIES • TECHNICAL TAKEAWAYS")

    add_card(s13, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_tm = s13.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tftm = tb_tm.text_frame
    tftm.word_wrap = True
    ptm = tftm.paragraphs[0]
    ptm.text = "Individual Contributions Breakdown"
    ptm.font.bold = True
    ptm.font.size = Pt(15)
    ptm.font.color.rgb = ACCENT_BLUE
    ptm.space_after = Pt(12)

    roles = [
        ("Team Lead (Architecture & Agentic Workflows): ", "Designed LangGraph state machine, dynamic complexity routing, Groq GPT-OSS-120B integration, and Next.js dark-mode frontend."),
        ("Member 2 (Information Retrieval & Math): ", "Engineered pure Python Tokenizer, Suffix Stemmer, Okapi BM25 ranking algorithm, and Reciprocal Rank Fusion combiner from scratch."),
        ("Member 3 (Adversarial Security & Benchmarking): ", "Engineered 4-layer injection taxonomy, leetspeak unmasker, compounding risk scorer, and empirical benchmark evaluation suites.")
    ]
    for h, b in roles:
        p = tftm.add_paragraph()
        r1 = p.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    add_card(s13, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_lr = s13.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tflr = tb_lr.text_frame
    tflr.word_wrap = True
    plr = tflr.paragraphs[0]
    plr.text = "Key Academic & Engineering Learnings"
    plr.font.bold = True
    plr.font.size = Pt(15)
    plr.font.color.rgb = ACCENT_EMERALD
    plr.space_after = Pt(12)

    learnings = [
        ("Probabilistic IR Foundations: ", "Understood why raw BM25 and dense embeddings cannot be linearly combined, and how RRF ordinal rank summation preserves search stability."),
        ("Adaptive Compute Efficiency: ", "Validated Singh et al.'s survey thesis: routing straightforward queries directly saves 72% compute latency without sacrificing factual grounding."),
        ("Deterministic vs LLM Guardrails: ", "Learned that LLM-based guardrails add roundtrip latency and are prone to recursive jailbreaks. Deterministic character-level de-obfuscation provides microsecond security guarantees.")
    ]
    for h, b in learnings:
        p = tflr.add_paragraph()
        r1 = p.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.color.rgb = TEXT_LIGHT
        r1.font.size = Pt(11)
        r2 = p.add_run()
        r2.text = b
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(10.5)
        p.space_after = Pt(8)

    prs.save(output_path)
    print(f"Presentation successfully created at: {output_path}")

if __name__ == "__main__":
    create_deck()
