import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import { ReviewStateAnnotation } from "../state.ts";
import type { ReviewResult } from "../state.ts";

const PRAISE_LOGGER_PROMPT = `You are a testimonial curator. Your job is to:

1. Extract the most impactful quote from the positive review
2. Summarize the key positive sentiment
3. Rate the testimonial value (high/medium/low)
4. Suggest where this testimonial could be used (landing page, social, etc.)

Keep the original voice of the user when extracting quotes.`;

export const praiseLoggerNode = async (state: typeof ReviewStateAnnotation.State) => {
  const praiseReviews = state.categorized_reviews.praise;

  if (!praiseReviews || praiseReviews.length === 0) {
    return {
      messages: [new AIMessage({ content: "No praise to log." })],
    };
  }

  const llm = new ChatOpenAI({ modelName: "gpt-5.2", temperature: 0 });

  const results: ReviewResult[] = [];
  const messages = [];

  // Process all praise reviews
  for (const review of praiseReviews) {
    const response = await llm.invoke([
      new SystemMessage(PRAISE_LOGGER_PROMPT),
      new HumanMessage(`Review Text: ${review.text}\nRating: ${review.rating}`),
    ]);

    const result: ReviewResult = {
      id: review.id,
      category: "praise",
      action_taken: "Logged as testimonial",
      details: {
        testimonial: response.content,
      },
    };

    results.push(result);
    messages.push(response);
  }

  console.log(`Logged ${results.length} testimonials`);

  return {
    praise_results: results,
    messages: messages,
  };
};
