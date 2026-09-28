import { Worker } from "bullmq";

import { getenv } from "../../config/env.js";
import { schedulerQueue } from "./scheduler.queue.js";
import { SchedulerPipeline } from "./schedulerPipeline.js";

const pipeline = new SchedulerPipeline();

export const schedulerWorker = new Worker(
  schedulerQueue.name,

  async (job) => {
    const { jobId, userId } = job.data;

    console.log(
      `[Scheduler Worker] Processing job ${jobId} for user ${userId}`,
    );

    await pipeline.schedule({ jobId, userId });
  },

  {
    connection: {
      host: getenv("REDIS_HOST"),
      port: Number(getenv("REDIS_PORT")),
    },
  },
);

schedulerWorker.on("completed", (job) => {
  console.log(
    `[Scheduler Worker] Job ${job.id} completed`,
  );
});

schedulerWorker.on("failed", (job, err) => {
  console.error(
    `[Scheduler Worker] Job ${job?.id} failed:`,
    err,
  );
});

console.log("Scheduler Worker Started...");