import {
  AIMessage,
  HumanMessage,
  SystemMessage,
} from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import { ReviewStateAnnotation } from "../state.ts";
import type { ReviewResult } from "../state.ts";

const FEATURE_ANALYST_PROMPT = `
  You are a feature specification writer. Your job is to:

  1. Analyze the feature request from a user review
  2. Determine feasibility and value
  3. Write a brief feature specification including:
    - Feature name
    - Problem it solves
    - Proposed solution
    - User benefit
    - Implementation complexity (low/medium/high)
    - Priority recommendation

  Be concise and focus on business value and user impact.
`;

export const featureAnalystNode = async (
  state: typeof ReviewStateAnnotation.State
) => {
  const featureReviews = state.categorized_reviews.features;

  if (!featureReviews || featureReviews.length === 0) {
    return {
      messages: [new AIMessage({ content: "No feature requests to analyze." })],
    };
  }

  console.log(`Found ${featureReviews.length} feature requests - awaiting approval`);

  // Don't generate specs yet - wait for human approval first
  return {
    pending_approval: true,
  };
};

export const featureApprovalNode = async (
  state: typeof ReviewStateAnnotation.State
) => {
  const featureReviews = state.categorized_reviews.features;
  const approvedIds = state.approved_feature_ids || [];

  if (!state.approved || approvedIds.length === 0) {
    console.log("No features approved - skipping specification generation.");
    return {
      messages: [
        new AIMessage({
          content: "Feature requests rejected or none approved.",
        }),
      ],
      pending_approval: false,
    };
  }

  const llm = new ChatOpenAI({ modelName: "gpt-5.2", temperature: 0 });
  const results: ReviewResult[] = [];
  const messages = [];

  console.log(`Generating specifications for ${approvedIds.length} approved feature(s)...`);

  // Generate specs only for approved features
  for (const review of featureReviews) {
    if (approvedIds.includes(review.id)) {
      const response = await llm.invoke([
        new SystemMessage(FEATURE_ANALYST_PROMPT),
        new HumanMessage(
          `Review Text: ${review.text}\nRating: ${review.rating}`
        ),
      ]);

      const result: ReviewResult = {
        id: review.id,
        category: "feature",
        action_taken: "Feature spec generated and approved",
        details: {
          spec: response.content,
        },
      };

      results.push(result);
      messages.push(response);
    }
  }

  console.log(`Generated ${results.length} feature specification(s)`);

  return {
    feature_results: results,
    pending_approval: false,
    messages: messages,
  };
};
