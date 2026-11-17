import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface QuizResultItem {
  id: number;
  question: string;
  selectedOption: string;
  correctOption: string;
  isCorrect: boolean;
  explanation: string;
}

interface GenerateReportOptions {
  topic: string;
  totalQuestions: number;
  score: number;
  results: QuizResultItem[];
  studentName?: string;
}

export function generateQuizPDFReport(options: GenerateReportOptions) {
  const { topic, totalQuestions, score, results, studentName = "Student Learner" } = options;
  const percentage = Math.round((score / totalQuestions) * 100);

  // Diagnostic Categorization
  const correctItems = results.filter(r => r.isCorrect);
  const incorrectItems = results.filter(r => !r.isCorrect);

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4'
  });

  // Header Background Banner
  doc.setFillColor(30, 41, 59); // Slate-800
  doc.rect(0, 0, 595, 110, 'F');

  // Title
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.text('LLM Tutor: Diagnostic Performance Report', 40, 48);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(11);
  doc.setTextColor(199, 210, 254); // Indigo-200
  doc.text(`Comprehensive Mastery Assessment • Topic: ${topic}`, 40, 72);
  doc.text(`Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 40, 90);

  // Performance Summary Card
  doc.setDrawColor(226, 232, 240);
  doc.setFillColor(248, 250, 252);
  doc.roundedRect(40, 130, 515, 80, 8, 8, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.setTextColor(30, 41, 59);
  doc.text('Overall Assessment Score', 55, 155);

  doc.setFontSize(28);
  if (percentage >= 80) {
    doc.setTextColor(16, 185, 129); // Emerald-500
  } else if (percentage >= 50) {
    doc.setTextColor(245, 158, 11); // Amber-500
  } else {
    doc.setTextColor(239, 68, 68); // Rose-500
  }
  doc.text(`${percentage}%`, 55, 192);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(11);
  doc.setTextColor(71, 85, 105);
  doc.text(`Answered Correctly: ${score} of ${totalQuestions} Questions`, 170, 175);
  const masteryBand = percentage >= 80 ? "Mastery: Advanced" : (percentage >= 50 ? "Mastery: Intermediate" : "Mastery: Developing");
  doc.text(`Proficiency Classification: ${masteryBand}`, 170, 195);

  // Strengths and Focus Recommendations
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(15, 23, 42);
  doc.text('Diagnostic Competency Analysis', 40, 240);

  // Strength Box
  doc.setFillColor(236, 253, 245); // Emerald-50
  doc.setDrawColor(167, 243, 208); // Emerald-200
  doc.roundedRect(40, 255, 245, 110, 6, 6, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(6, 95, 70); // Emerald-800
  doc.text('Demonstrated Strengths', 50, 275);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(15, 23, 42);
  const strengthText = correctItems.length > 0 
    ? `Strong conceptual grasp demonstrated on ${correctItems.length} core concepts including algorithmic principles and foundational mechanics.`
    : "No areas scored 100% yet. Continued practice on foundational definitions will build baseline confidence.";
  doc.text(doc.splitTextToSize(strengthText, 225), 50, 295);

  // Focus Area Box
  doc.setFillColor(254, 242, 242); // Rose-50
  doc.setDrawColor(254, 202, 202); // Rose-200
  doc.roundedRect(310, 255, 245, 110, 6, 6, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(153, 27, 27); // Rose-800
  doc.text('Recommended Focus Areas', 320, 275);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(15, 23, 42);
  const focusText = incorrectItems.length > 0
    ? `Review needed for ${incorrectItems.length} specific items. Pay closer attention to subtle design differences, hyperparameters, and edge conditions.`
    : "Outstanding performance! You have mastered all tested areas in this module. Ready for advanced multi-hop reasoning.";
  doc.text(doc.splitTextToSize(focusText, 225), 320, 295);

  // Detailed Question-by-Question Breakdown Table
  const tableData = results.map(r => [
    `Q${r.id}`,
    r.question,
    r.selectedOption,
    r.correctOption,
    r.isCorrect ? "CORRECT" : "INCORRECT",
    r.explanation
  ]);

  autoTable(doc, {
    startY: 385,
    margin: { left: 40, right: 40 },
    head: [['#', 'Question', 'Chosen', 'Key', 'Status', 'Educational Explanation']],
    body: tableData,
    theme: 'striped',
    headStyles: {
      fillColor: [79, 70, 229], // Indigo-600
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 8
    },
    styles: {
      fontSize: 8,
      cellPadding: 6,
      overflow: 'linebreak'
    },
    columnStyles: {
      0: { cellWidth: 25 },
      1: { cellWidth: 140 },
      2: { cellWidth: 35, halign: 'center' },
      3: { cellWidth: 30, halign: 'center' },
      4: { cellWidth: 55, fontStyle: 'bold' },
      5: { cellWidth: 190 }
    },
    didParseCell: (data) => {
      if (data.column.index === 4) {
        if (data.cell.text[0] === 'CORRECT') {
          data.cell.styles.textColor = [16, 185, 129];
        } else {
          data.cell.styles.textColor = [239, 68, 68];
        }
      }
    }
  });

  // Save the PDF
  const sanitizedTopic = topic.replace(/[^a-zA-Z0-9]/g, '_');
  doc.save(`LLM_Tutor_Report_${sanitizedTopic}.pdf`);
}
