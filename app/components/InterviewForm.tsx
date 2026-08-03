"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";


type PracticeQuestion = {
  question: string;
  category: string;
  source_type: string;
  difficulty: string;
  reason_selected: string;
  follow_up_questions: string[];
};

type StartInterviewResponse = {
  company: string;
  role: string;
  level: string;
  duration_minutes: number;
  questions: PracticeQuestion[];
};

export default function InterviewForm() {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");

  const router = useRouter();
  const [formError, setFormError] = useState("");
  
  const [isStarting, setIsStarting] = useState(false);

  const [durationMinutes, setDurationMinutes] = useState("auto");

  async function startInterview() {
  if (!company.trim() || !role.trim() || !level) {
    setFormError("Enter a company, role, and level.");
    return;
  }

  setIsStarting(true);
  setFormError("");

  try {
    const response = await fetch(
      "http://localhost:8000/interview/start",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
  company: company.trim(),
  role: role.trim(),
  level,
  duration_minutes:
    durationMinutes === "auto"
      ? null
      : Number(durationMinutes),
}),
      }
    );

    if (!response.ok) {
      throw new Error("Could not generate interview questions.");
    }

    const data: StartInterviewResponse =
      await response.json();

    sessionStorage.setItem(
      "interviewData",
      JSON.stringify(data)
    );

    router.push("/interview");
  } catch (error) {
    console.error(error);

    setFormError(
      "Could not generate the interview. Make sure FastAPI is running."
    );
  } finally {
    setIsStarting(false);
  }
}

  return (
    <div className="w-96 rounded-xl bg-white p-8 shadow-xl">
      <h1 className="mb-6 text-3xl font-bold">
        Interview Intelligence
      </h1>

      <input
        placeholder="enter company..."
        className="mb-4 w-full rounded-lg border p-3"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
      />

      <input
        value={role}
        onChange={(e) => setRole(e.target.value)}
        placeholder="enter role..."
        className="mb-4 w-full rounded-lg border p-3"
      />

      <select
        value={level}
        onChange={(e) => setLevel(e.target.value)}
        className="mb-4 w-full rounded-lg border p-3"
      >
        <option value="">Select level</option>
        <option value="intern">Intern</option>
        <option value="new grad">New Grad</option>
        <option value="mid">Mid Level</option>
        <option value="senior">Senior</option>
      </select>

      <select
  value={durationMinutes}
  onChange={(e) => setDurationMinutes(e.target.value)}
  className="mb-4 w-full rounded-lg border p-3"
>
  <option value="auto">Auto — Recommended</option>
  <option value="20">20 minutes</option>
  <option value="30">30 minutes</option>
  <option value="45">45 minutes</option>
  <option value="60">60 minutes</option>
</select>

{formError && (
  <p className="mb-3 text-sm text-red-600">
    {formError}
  </p>
)}

  

      <button
        type="button"
        onClick={startInterview}
        disabled={isStarting}
        className="mt-3 w-full rounded-lg bg-blue-600 p-3 text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isStarting
          ? "Generating interview..."
          : "Start Interview"}
      </button>

    </div>
  );
}