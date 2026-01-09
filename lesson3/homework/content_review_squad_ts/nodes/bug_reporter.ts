import {
  AIMessage,
  HumanMessage,
  SystemMessage,
} from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ReviewStateAnnotation } from "../state.ts";
import type { ReviewResult } from "../state.ts";

const BUG_REPORTER_PROMPT = `You are a bug report specialist. Your job is to:

1. Analyze the user's bug report
2. Extract key information:
   - Summary (one line)
   - Steps to reproduce (if mentioned)
   - Expected behavior
   - Actual behavior
   - Severity (critical/high/medium/low)
3. Format as a structured bug report

Be concise and technical. Focus on actionable information.`;

// Mock GitHub issue creation tool
const createGithubIssue = tool(
  async ({ title, body, labels }) => {
    const issueNum = Math.floor(Math.random() * 900) + 100;
    return {
      issue_number: issueNum,
      url: `https://github.com/example/repo/issues/${issueNum}`,
      status: "created",
      title,
      body,
      labels,
    };
  },
  {
    name: "create_github_issue",
    description: "Create a GitHub issue for the bug report.",
    schema: z.object({
      title: z.string().describe("Issue title"),
      body: z.string().describe("Issue body in markdown"),
      labels: z
        .array(z.string())
        .describe('Labels to apply (e.g., ["bug", "high-priority"])'),
    }),
  }
);

export const bugReporterNode = async (
  state: typeof ReviewStateAnnotation.State
) => {
  const bugReviews = state.categorized_reviews.bugs;

  if (!bugReviews || bugReviews.length === 0) {
    return {
      messages: [new AIMessage({ content: "No bug reviews to process." })],
    };
  }

  const llm = new ChatOpenAI({ modelName: "gpt-5-mini" });
  const llmWithTools = llm.bindTools([createGithubIssue]);

  const results: ReviewResult[] = [];
  const messages = [];

  // Process all bug reviews
  for (const review of bugReviews) {
    const response = await llmWithTools.invoke([
      new SystemMessage(BUG_REPORTER_PROMPT),
      new HumanMessage(
        `Review Text: ${review.text}\nRating: ${review.rating}`
      ),
    ]);

    const result: ReviewResult = {
      id: review.id,
      category: "bug",
      action_taken: "Created structured report/GitHub issue",
      details: {
        content: response.content,
        tool_calls: response.tool_calls,
      },
    };

    results.push(result);
    messages.push(response);
  }

  console.log(`Processed ${results.length} bug reports`);

  return {
    bug_results: results,
    messages: messages,
  };
};
