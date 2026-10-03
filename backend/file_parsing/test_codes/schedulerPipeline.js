import Redis from "ioredis";

import User from "../user/user.model.js";
import Source from "../sources/source.model.js";
import { JobModel } from "../job/job.repository.js";
import { applyQueue } from "../apply/apply.queue.js"; 

import { getenv } from "../../config/env.js";

const redis = new Redis({
  host: getenv("REDIS_HOST"),
  port: Number(getenv("REDIS_PORT")),
});

export class SchedulerPipeline {
  async schedule({ userId, jobId }) {
    console.log(
      `[Scheduler Pipeline] Scheduling job ${jobId} for user ${userId}`,
    );

    const [user, job] = await Promise.all([
      User.findById(userId),
      JobModel.findById(jobId),
    ]);

    if (!user) {
      console.log(`[Scheduler Pipeline] User ${userId} not found`);
      return;
    }

    if (user.status !== "active") {
      console.log(`[Scheduler Pipeline] User ${userId} is not active`);
      return;
    }

    if (!job) {
      console.log(`[Scheduler Pipeline] Job ${jobId} not found`);
      throw new Error(`[Scheduler Pipeline] Job ${jobId} not found`);
    }

    const source = await Source.findById(job.sourceId);

    if (!source || !source.active) {
      console.log(
        `[Scheduler Pipeline] Source not found/inactive: ${source.name}`,
      );
      return;
    }

    const scheduledAt = await this.calculateNextTime({
      user,
      source,
    });

    const delay = Math.max(0, scheduledAt.getTime() - Date.now());

    console.log(
      `[Scheduler Pipeline] Job ${jobId} scheduled at ${scheduledAt.toISOString()}`,
    );

    console.log(
      `[Scheduler Pipeline] Delay: ${delay}ms`,
    );

    await applyQueue.add(
      "apply-queue",
      {
        userId,
        jobId,
      },
      {
        delay,
      },
    );

    console.log(
      `[Scheduler Pipeline] Job ${jobId} pushed to apply queue`,
    );
  }

  async calculateNextTime({ user, source }) {
    const now = Date.now();

    /*
     * ==========================================
     * USER DAILY LIMIT
     * ==========================================
     *
     * applications_today is maintained by the
     * Apply module.
     */

    let userResetAt =
      user.applications_today_reset_at.getTime();

    if (now >= userResetAt) {
      console.log(
        `[Scheduler] Daily counter expired for user ${user._id}`,
      );

      // We don't need to update applications_today here.
      // Apply module owns the actual application counter.

      userResetAt =
        now + Number(getenv("SCHEDULER_DAILY_RESET_INTERVAL_HOURS") || 24) * 60 * 60 * 1000;
    }

    if (
      user.max_applications_per_day > 0 &&
      user.applications_today >=
        user.max_applications_per_day
    ) {
      console.log(
        `[Scheduler] User ${user._id} reached daily limit`,
      );

      return new Date(userResetAt);
    }

    /*
     * ==========================================
     * USER LAST SCHEDULED TIME
     * ==========================================
     *
     * For now we use a fixed interval.
     *
     * You can later move this interval into
     * User preferences/config.
     */

    const USER_INTERVAL = Number(
      getenv("SCHEDULER_APPLICATION_INTERVAL_MINUTES") || 5,
    );

    const userKey =
      `scheduler:user:${user._id}:last-scheduled`;

    const lastUserTime =
      await redis.get(userKey);

    let userNextTime = now;

    if (lastUserTime) {
      userNextTime =
        Number(lastUserTime) +
        USER_INTERVAL * 60 * 1000;
    }

    /*
     * ==========================================
     * SOURCE LIMIT
     * ==========================================
     *
     * Source stores:
     *
     * max_applications_per_hour
     *
     * We maintain scheduled timestamps in Redis
     * so future applications are also considered.
     */

    const sourceKey =
      `scheduler:source:${source._id}:applications`;

    const sourceRateLimitWindowHours = Number(
      getenv("SCHEDULER_SOURCE_RATE_LIMIT_WINDOW_HOURS") || 1,
    );
    const sourceRateLimitWindowMs = sourceRateLimitWindowHours * 60 * 60 * 1000;
    const oneHourAgo = now - sourceRateLimitWindowMs;

    // Remove old scheduled timestamps.
    await redis.zremrangebyscore(
      sourceKey,
      0,
      oneHourAgo,
    );

    const sourceApplications =
      await redis.zrange(
        sourceKey,
        0,
        -1,
        "WITHSCORES",
      );

    const sourceTimes = [];

    for (
      let i = 1;
      i < sourceApplications.length;
      i += 2
    ) {
      sourceTimes.push(
        Number(sourceApplications[i]),
      );
    }

    let sourceNextTime = now;

    if (
      source.max_applications_per_hour > 0 &&
      sourceTimes.length >=
        source.max_applications_per_hour
    ) {
      const oldest =
        sourceTimes[0];

      sourceNextTime = oldest + sourceRateLimitWindowMs;

      console.log(
        `[Scheduler] Source ${source.name} hourly limit reached`,
      );
    }

    /*
     * ==========================================
     * FINAL TIME
     * ==========================================
     */

    const scheduledTime = Math.max(
      now,
      userNextTime,
      sourceNextTime,
    );

    /*
     * ==========================================
     * RESERVE SCHEDULING STATE
     * ==========================================
     */

    await redis.set(
      userKey,
      String(scheduledTime),
    );

    /*
     * Only keep source reservations for
     * source-rate-limit calculation.
     */

    const reservationId =
      `${user._id}:${Date.now()}:${Math.random()}`;

    await redis.zadd(
      sourceKey,
      scheduledTime,
      reservationId,
    );

    console.log(
      `[Scheduler] User next available: ${new Date(userNextTime).toISOString()}`,
    );

    console.log(
      `[Scheduler] Source next available: ${new Date(sourceNextTime).toISOString()}`,
    );

    console.log(
      `[Scheduler] Final slot: ${new Date(scheduledTime).toISOString()}`,
    );

    return new Date(scheduledTime);
  }
}
