"use client";

import { useEffect, useRef, useState } from "react";

type PracticeQuestion = {
  question: string;
  category: string;
  source_type: string;
  difficulty: string;
  reason_selected: string;
  follow_up_questions: string[];
};

type Message = {
  speaker: "interviewer" | "candidate";
  text: string;
};

type InterviewApiResponse = {
  reply: string;
  action: "stay_on_question" | "next_question";
  response_type:
    | "clarification"
    | "partial_answer"
    | "complete_answer"
    | "off_topic";
};

type StartInterviewResponse = {
  company: string;
  role: string;
  level: string;
  duration_minutes: number;
  questions: PracticeQuestion[];
};

export default function InterviewPage() {
  const [questionIndex, setQuestionIndex] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState("");

  const currentQuestion =
    questions[questionIndex]?.question ?? "";

  const currentQuestionData =
    questions[questionIndex];

  const [interviewStarted, setInterviewStarted] =
    useState(false);

  const [interviewComplete, setInterviewComplete] =
    useState(false);

  const [cameraError, setCameraError] = useState("");

  const videoRef = useRef<HTMLVideoElement>(null);

  const [answer, setAnswer] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [answerError, setAnswerError] = useState("");

  const [submittedAnswers, setSubmittedAnswers] =
    useState<string[]>([]);

  const [messages, setMessages] = useState<Message[]>([]);

  const [isResponding, setIsResponding] =
    useState(false);

  const [apiError, setApiError] = useState("");

  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");

  const [durationMinutes, setDurationMinutes] =
    useState(0);

  const [secondsRemaining, setSecondsRemaining] =
    useState(0);

  const interviewContextReady = Boolean(
    company.trim() &&
      role.trim() &&
      level.trim() &&
      durationMinutes > 0
  );

  const timerMinutes = Math.floor(
    secondsRemaining / 60
  );

  const timerSeconds = secondsRemaining % 60;

  const formattedTime = `${timerMinutes}:${timerSeconds
    .toString()
    .padStart(2, "0")}`;

  function speakText(
    text: string,
    onFinished?: () => void
  ) {
    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);

    speech.onstart = () => {
      setIsSpeaking(true);
    };

    speech.onend = () => {
      setIsSpeaking(false);
      onFinished?.();
    };

    speech.onerror = () => {
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(speech);
  }

  function speakQuestion() {
    speakText(currentQuestion);
  }

  function stopCamera() {
    const stream = videoRef.current?.srcObject;

    if (stream instanceof MediaStream) {
      stream.getTracks().forEach((track) => {
        track.stop();
      });
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  function finishInterview() {
    window.speechSynthesis.cancel();

    setIsSpeaking(false);
    setIsListening(false);
    setInterviewComplete(true);

    stopCamera();
  }

  function advanceToNextQuestion(fromIndex: number) {
    const isLastQuestion =
      fromIndex === questions.length - 1;

    if (isLastQuestion) {
      finishInterview();
      return;
    }

    const nextIndex = fromIndex + 1;
    const nextQuestion =
      questions[nextIndex].question;

    setQuestionIndex(nextIndex);

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        speaker: "interviewer",
        text: nextQuestion,
      },
    ]);

    speakText(nextQuestion);
  }

  async function startInterview() {
    if (
      questions.length === 0 ||
      !interviewContextReady
    ) {
      return;
    }

    try {
      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      setInterviewStarted(true);
      setCameraError("");

      setMessages([
        {
          speaker: "interviewer",
          text: currentQuestion,
        },
      ]);

      speakQuestion();
    } catch (error) {
      console.error(error);

      setCameraError(
        "Camera or microphone access was denied. Check your browser permissions."
      );
    }
  }

  function startListening() {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setAnswerError(
        "Speech recognition is not supported in this browser."
      );
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      setAnswerError("");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);

      setAnswerError(
        "Could not recognize your speech. Try again."
      );
    };

    recognition.onresult = (event: any) => {
      const transcript =
        event.results[0][0].transcript;

      setAnswer((currentAnswer) => {
        return `${currentAnswer} ${transcript}`.trim();
      });
    };

    recognition.start();
  }

  async function submitAnswer() {
    if (!answer.trim()) {
      setAnswerError(
        "Say or type an answer before submitting."
      );
      return;
    }

    const candidateAnswer = answer.trim();

    setSubmittedAnswers((currentAnswers) => [
      ...currentAnswers,
      candidateAnswer,
    ]);

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        speaker: "candidate",
        text: candidateAnswer,
      },
    ]);

    setAnswer("");
    setAnswerError("");
    setApiError("");
    setIsResponding(true);

    try {
      const response = await fetch(
        "http://localhost:8000/interview/respond",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            company,
            role,
            level,

            duration_minutes: durationMinutes,
            seconds_remaining: secondsRemaining,

            current_question: currentQuestion,

            question_category:
              currentQuestionData?.category ?? "other",

            question_difficulty:
              currentQuestionData?.difficulty ??
              "medium",

            suggested_follow_ups:
              currentQuestionData
                ?.follow_up_questions ?? [],

            candidate_response: candidateAnswer,

            conversation_history: messages,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "The interview backend returned an error."
        );
      }

      const data: InterviewApiResponse =
        await response.json();

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          speaker: "interviewer",
          text: data.reply,
        },
      ]);

      if (data.action === "next_question") {
        speakText(data.reply, () => {
          advanceToNextQuestion(questionIndex);
        });
      } else {
        speakText(data.reply);
      }
    } catch (error) {
      console.error(error);

      setApiError(
        "Could not contact the interviewer backend. Make sure FastAPI is running."
      );
    } finally {
      setIsResponding(false);
    }
  }

  useEffect(() => {
    try {
      const savedInterview =
        sessionStorage.getItem("interviewData");

      if (!savedInterview) {
        setQuestionsError(
          "No interview was found. Return to the setup page."
        );
        return;
      }

      const data: StartInterviewResponse =
        JSON.parse(savedInterview);

      const savedDuration =
        data.duration_minutes ?? 45;

      setCompany(data.company);
      setRole(data.role);
      setLevel(data.level);
      setDurationMinutes(savedDuration);
      setSecondsRemaining(savedDuration * 60);
      setQuestions(data.questions);
    } catch (error) {
      console.error(error);

      setQuestionsError(
        "The interview data could not be loaded."
      );
    } finally {
      setQuestionsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!interviewStarted || interviewComplete) {
      return;
    }

    const timer = window.setInterval(() => {
      setSecondsRemaining((currentSeconds) => {
        if (currentSeconds <= 1) {
          window.clearInterval(timer);
          window.speechSynthesis.cancel();

          setIsSpeaking(false);
          setIsListening(false);
          setInterviewComplete(true);

          const stream =
            videoRef.current?.srcObject;

          if (stream instanceof MediaStream) {
            stream.getTracks().forEach((track) => {
              track.stop();
            });
          }

          if (videoRef.current) {
            videoRef.current.srcObject = null;
          }

          return 0;
        }

        return currentSeconds - 1;
      });
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [interviewStarted, interviewComplete]);

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();

      const stream = videoRef.current?.srcObject;

      if (stream instanceof MediaStream) {
        stream.getTracks().forEach((track) => {
          track.stop();
        });
      }
    };
  }, []);

  return (
    <main className="min-h-screen bg-gray-950 px-6 py-10 text-white">
      {questionsLoading && (
        <p className="text-center text-gray-400">
          Loading interview questions...
        </p>
      )}

      {questionsError && (
        <p className="text-center text-red-400">
          {questionsError}
        </p>
      )}

      <div className="mx-auto w-full max-w-6xl">
        <h1 className="mb-2 text-center text-4xl font-bold">
          AI Interview
        </h1>

        <p className="mb-3 text-center text-gray-400">
          {company} · {role} · {level}
        </p>

        {durationMinutes > 0 && (
          <p className="mb-6 text-center text-sm text-gray-500">
            {durationMinutes}-minute interview
          </p>
        )}

        {interviewStarted && !interviewComplete && (
          <div className="mb-6 text-center">
            <p className="text-sm uppercase tracking-wider text-gray-400">
              Time remaining
            </p>

            <p className="text-3xl font-bold">
              {formattedTime}
            </p>
          </div>
        )}

        <section className="mb-8 rounded-3xl bg-gray-900 p-8 text-center">
          {!interviewStarted ? (
            <>
              <h2 className="mb-3 text-2xl font-semibold">
                Ready to begin?
              </h2>

              <p className="mb-6 text-gray-400">
                Your camera and microphone will be used
                during the interview.
              </p>

              <button
                type="button"
                onClick={startInterview}
                disabled={
                  questionsLoading ||
                  questions.length === 0 ||
                  !interviewContextReady
                }
                className="rounded-full bg-blue-600 px-8 py-4 font-semibold hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Start Interview
              </button>
            </>
          ) : interviewComplete ? (
            <>
              <h2 className="text-2xl font-semibold">
                Interview finished
              </h2>

              <p className="mt-3 text-gray-400">
                Your interview responses have been
                recorded.
              </p>
            </>
          ) : (
            <>
              <p className="mb-3 text-sm text-gray-400">
                Question {questionIndex + 1} of{" "}
                {questions.length}
              </p>

              <p className="text-2xl leading-relaxed">
                {currentQuestion}
              </p>
            </>
          )}

          {cameraError && (
            <p className="mt-5 text-red-400">
              {cameraError}
            </p>
          )}
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          <section className="flex min-h-96 flex-col items-center justify-center rounded-3xl bg-gray-900 p-8">
            <p className="mb-5 text-sm uppercase tracking-widest text-blue-400">
              Interviewer
            </p>

            <div
              className={`flex h-48 w-48 items-center justify-center rounded-full bg-blue-950 text-8xl ${
                isSpeaking
                  ? "animate-pulse ring-4 ring-blue-500"
                  : ""
              }`}
            >
              👩‍💼
            </div>

            <p className="mt-6 text-gray-400">
              {isSpeaking ? "Speaking..." : "Waiting"}
            </p>
          </section>

          <section className="relative min-h-96 overflow-hidden rounded-3xl bg-gray-900">
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="h-96 w-full object-cover"
            />

            {!interviewStarted && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                <p className="text-gray-400">
                  Your camera will appear here
                </p>
              </div>
            )}

            {interviewComplete && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                <p className="text-gray-400">
                  Interview complete
                </p>
              </div>
            )}

            <div className="absolute bottom-4 left-4 rounded-full bg-black/60 px-4 py-2 text-sm">
              You
            </div>
          </section>
        </div>

        {interviewComplete && (
          <section className="mt-8 rounded-3xl bg-gray-900 p-8 text-center">
            <h2 className="text-3xl font-bold">
              Interview Complete
            </h2>

            <p className="mt-3 text-gray-400">
              You submitted{" "}
              {submittedAnswers.length} responses.
            </p>
          </section>
        )}

        {interviewStarted && (
          <section className="mt-8 rounded-3xl bg-gray-900 p-8">
            <h2 className="mb-5 text-xl font-semibold">
              Conversation
            </h2>

            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.speaker === "interviewer"
                      ? "mr-auto max-w-3xl rounded-2xl bg-gray-800 p-4"
                      : "ml-auto max-w-3xl rounded-2xl bg-blue-600 p-4"
                  }
                >
                  <p className="mb-1 text-xs uppercase tracking-wide text-gray-300">
                    {message.speaker === "interviewer"
                      ? "Interviewer"
                      : "You"}
                  </p>

                  <p>{message.text}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {interviewStarted && !interviewComplete && (
          <section className="mt-8 rounded-3xl bg-gray-900 p-8">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                Your Answer
              </h2>

              <p className="text-sm text-gray-400">
                {isListening
                  ? "Listening..."
                  : "Microphone ready"}
              </p>
            </div>

            <textarea
              value={answer}
              onChange={(event) =>
                setAnswer(event.target.value)
              }
              placeholder="Your spoken answer will appear here. You can also type or edit it."
              className="min-h-36 w-full resize-none rounded-2xl border border-gray-700 bg-gray-800 p-4 text-white outline-none focus:border-blue-500"
            />

            {answerError && (
              <p className="mt-3 text-sm text-red-400">
                {answerError}
              </p>
            )}

            {apiError && (
              <p className="mt-3 text-sm text-red-400">
                {apiError}
              </p>
            )}

            <div className="mt-5 flex justify-end gap-4">
              <button
                type="button"
                onClick={startListening}
                disabled={
                  isListening ||
                  isSpeaking ||
                  isResponding
                }
                className="rounded-full bg-gray-700 px-6 py-3 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isListening
                  ? "Listening..."
                  : "Speak Answer"}
              </button>

              <button
                type="button"
                onClick={submitAnswer}
                disabled={
                  !answer.trim() ||
                  isResponding ||
                  isSpeaking
                }
                className="rounded-full bg-blue-600 px-6 py-3 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isResponding
                  ? "Interviewer thinking..."
                  : "Submit Answer"}
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}