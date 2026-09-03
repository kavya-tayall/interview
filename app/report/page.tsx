"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";


type QuestionFeedback = {
  question_index: number;
  question: string;
  score: number;
  what_went_well: string[];
  what_to_improve: string[];
  better_answer_outline: string[];
};


type InterviewReport = {
  overall_score: number;

  readiness:
    | "needs_practice"
    | "developing"
    | "interview_ready"
    | "strong";

  summary: string;
  overall_strengths: string[];
  overall_improvements: string[];
  question_feedback: QuestionFeedback[];
};


export default function ReportPage() {
  const router = useRouter();

  const [report, setReport] =
    useState<InterviewReport | null>(null);

  const [error, setError] = useState("");


  useEffect(() => {
    try {
      const savedReport =
        sessionStorage.getItem(
          "interviewReport"
        );

      if (!savedReport) {
        setError(
          "No interview report was found."
        );

        return;
      }

      const parsedReport: InterviewReport =
        JSON.parse(savedReport);

      setReport(parsedReport);
    } catch (error) {
      console.error(error);

      setError(
        "The interview report could not be loaded."
      );
    }
  }, []);


  if (error) {
    return (
      <main className="min-h-screen bg-gray-950 px-6 py-10 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl font-bold">
            Interview Report
          </h1>

          <p className="mt-6 text-red-400">
            {error}
          </p>

          <button
            type="button"
            onClick={() => router.push("/")}
            className="mt-8 rounded-full bg-blue-600 px-6 py-3 font-semibold"
          >
            Start New Interview
          </button>
        </div>
      </main>
    );
  }


  if (!report) {
    return (
      <main className="min-h-screen bg-gray-950 px-6 py-10 text-white">
        <p className="text-center text-gray-400">
          Loading report...
        </p>
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-gray-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-center text-4xl font-bold">
          Interview Report
        </h1>

        <section className="mt-10 rounded-3xl bg-gray-900 p-8 text-center">
          <p className="text-sm uppercase tracking-widest text-gray-400">
            Overall Score
          </p>

          <p className="mt-3 text-6xl font-bold text-blue-400">
            {report.overall_score}
            <span className="text-2xl text-gray-500">
              /100
            </span>
          </p>

          <p className="mt-4 text-lg capitalize">
            {report.readiness.replaceAll(
              "_",
              " "
            )}
          </p>

          <p className="mx-auto mt-6 max-w-3xl text-gray-300">
            {report.summary}
          </p>
        </section>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <section className="rounded-3xl bg-gray-900 p-8">
            <h2 className="text-2xl font-semibold text-green-400">
              Strengths
            </h2>

            <ul className="mt-5 space-y-3 text-gray-300">
              {report.overall_strengths.map(
                (strength, index) => (
                  <li key={index}>
                    • {strength}
                  </li>
                )
              )}
            </ul>
          </section>

          <section className="rounded-3xl bg-gray-900 p-8">
            <h2 className="text-2xl font-semibold text-yellow-400">
              Areas to Improve
            </h2>

            <ul className="mt-5 space-y-3 text-gray-300">
              {report.overall_improvements.map(
                (improvement, index) => (
                  <li key={index}>
                    • {improvement}
                  </li>
                )
              )}
            </ul>
          </section>
        </div>

        <section className="mt-8">
          <h2 className="mb-6 text-3xl font-bold">
            Question Feedback
          </h2>

          <div className="space-y-6">
            {report.question_feedback.map(
              (feedback) => (
                <article
                  key={feedback.question_index}
                  className="rounded-3xl bg-gray-900 p-8"
                >
                  <div className="flex items-start justify-between gap-6">
                    <div>
                      <p className="text-sm text-gray-500">
                        Question{" "}
                        {feedback.question_index + 1}
                      </p>

                      <h3 className="mt-2 text-xl font-semibold">
                        {feedback.question}
                      </h3>
                    </div>

                    <p className="shrink-0 text-3xl font-bold text-blue-400">
                      {feedback.score}/10
                    </p>
                  </div>

                  <div className="mt-8 grid gap-6 md:grid-cols-3">
                    <div>
                      <h4 className="font-semibold text-green-400">
                        What went well
                      </h4>

                      <ul className="mt-3 space-y-2 text-gray-300">
                        {feedback.what_went_well.map(
                          (item, index) => (
                            <li key={index}>
                              • {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-yellow-400">
                        What to improve
                      </h4>

                      <ul className="mt-3 space-y-2 text-gray-300">
                        {feedback.what_to_improve.map(
                          (item, index) => (
                            <li key={index}>
                              • {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-blue-400">
                        Better answer outline
                      </h4>

                      <ol className="mt-3 space-y-2 text-gray-300">
                        {feedback.better_answer_outline.map(
                          (item, index) => (
                            <li key={index}>
                              {index + 1}. {item}
                            </li>
                          )
                        )}
                      </ol>
                    </div>
                  </div>
                </article>
              )
            )}
          </div>
        </section>

        <div className="mt-10 text-center">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="rounded-full bg-blue-600 px-8 py-4 font-semibold hover:bg-blue-500"
          >
            Start New Interview
          </button>
        </div>
      </div>
    </main>
  );
}