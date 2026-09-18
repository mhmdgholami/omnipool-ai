import assert from "node:assert/strict";
import test from "node:test";

globalThis.window = {
  setTimeout,
  clearTimeout,
};

const { request } = await import("../frontend/api.js");

test("request forwards user cancellation to fetch", async () => {
  let receivedSignal;

  globalThis.fetch = (_path, options) => {
    receivedSignal = options.signal;
    return new Promise((_resolve, reject) => {
      options.signal.addEventListener(
        "abort",
        () => {
          const error = new Error("aborted");
          error.name = "AbortError";
          reject(error);
        },
        { once: true },
      );
    });
  };

  const controller = new AbortController();
  const pending = request("/api/v1/generate", {
    method: "POST",
    body: { title: "test" },
    timeoutMs: 1000,
    signal: controller.signal,
  });

  controller.abort();

  await assert.rejects(
    pending,
    (error) => error.name === "AbortError",
  );
  assert.equal(receivedSignal.aborted, true);
});

test("request timeout also aborts a stalled fetch", async () => {
  globalThis.fetch = (_path, options) =>
    new Promise((_resolve, reject) => {
      options.signal.addEventListener(
        "abort",
        () => {
          const error = new Error("timeout");
          error.name = "AbortError";
          reject(error);
        },
        { once: true },
      );
    });

  await assert.rejects(
    request("/api/slow", { timeoutMs: 5 }),
    (error) => error.name === "AbortError",
  );
});
