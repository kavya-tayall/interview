type ReportRequestData = {
  company: string;
  role: string;
  level: string;
  duration_minutes: number;

  questions: unknown[];
  messages: unknown[];

  completed_reason:
    | "finished_questions"
    | "time_expired";
};


export async function requestInterviewReport(
  reportData: ReportRequestData
) {
  const response = await fetch(
    "http://localhost:8000/interview/report",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(reportData),
    }
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    console.error(
      "Report API error:",
      errorText
    );

    throw new Error(
      "The report backend returned an error."
    );
  }

  return response.json();
}