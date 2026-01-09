import { Annotation, MessagesAnnotation } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";

export interface Review {
  id: number;
  text: string;
  rating: number;
}

export type ReviewCategory = "bug" | "feature" | "praise";

export type ReviewResult = {
  id: number;
  category: ReviewCategory;
  action_taken: string;
  details: Record<string, any>;
};

export interface CategorizedReviews {
  bugs: Review[];
  features: Review[];
  praise: Review[];
}

export const ReviewStateAnnotation = Annotation.Root({
  // ...MessagesAnnotation.spec,
  messages: MessagesAnnotation.spec.messages,
  
  // === INPUT ===
  reviews: Annotation<Review[]>({
    reducer: (x, y) => y ?? x,
    default: () => [],
  }),

  // === TRIAGE ===
  categorized_reviews: Annotation<CategorizedReviews>({
    reducer: (x, y) => y ?? x,
    default: () => ({ bugs: [], features: [], praise: [] }),
  }),

  // === AGENT RESULTS ===
  bug_results: Annotation<ReviewResult[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  feature_results: Annotation<ReviewResult[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  praise_results: Annotation<ReviewResult[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),

  // === HUMAN REVIEW ===
  pending_approval: Annotation<boolean>({
    reducer: (x, y) => y ?? x,
    default: () => false,
  }),
  approved: Annotation<boolean>({
    reducer: (x, y) => y ?? x,
    default: () => false,
  }),
  approved_feature_ids: Annotation<number[]>({
    reducer: (x, y) => y ?? x,
    default: () => [],
  }),

  // === SYNTHESIS ===
  summary_report: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});
