import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import { ReviewStateAnnotation } from "../state.ts";
import type { Review, CategorizedReviews } from "../state.ts";

const TRIAGE_SYSTEM_PROMPT = `You are a review triage specialist. Your job is to classify
product reviews into one of three categories:

1. BUG - The review describes a bug, error, crash, or something not working correctly
2. FEATURE - The review requests a new feature or improvement
3. PRAISE - The review is positive feedback, testimonial, or general appreciation

Analyze the review text and rating. Return ONLY one word: BUG, FEATURE, or PRAISE.`;

export const triageNode = async (state: typeof ReviewStateAnnotation.State) => {
  const reviews = state.reviews;

  if (!reviews || reviews.length === 0) {
    return {
      messages: [new AIMessage({ content: "No reviews to classify." })],
      categorized_reviews: { bugs: [], features: [], praise: [] },
    };
  }

  const llm = new ChatOpenAI({ modelName: "gpt-5-mini" });

  const categorizedReviews: CategorizedReviews = {
    bugs: [],
    features: [],
    praise: [],
  };

  const messages = [];

  // Process all reviews
  for (const review of reviews) {
    const response = await llm.invoke([
      new SystemMessage(TRIAGE_SYSTEM_PROMPT),
      new HumanMessage(`Review Text: ${review.text}\nRating: ${review.rating}`),
    ]);

    const category = response.content.toString().trim().toUpperCase();
    
    if (category === "BUG") {
      categorizedReviews.bugs.push(review);
    } else if (category === "FEATURE") {
      categorizedReviews.features.push(review);
    } else {
      categorizedReviews.praise.push(review);
    }

    messages.push(response);
  }

  console.log(`Triaged ${reviews.length} reviews: ${categorizedReviews.bugs.length} bugs, ${categorizedReviews.features.length} features, ${categorizedReviews.praise.length} praise`);

  return {
    categorized_reviews: categorizedReviews,
    messages: messages,
  };
};
