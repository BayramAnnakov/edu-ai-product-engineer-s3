import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import { ReviewStateAnnotation } from "../state.ts";

const SUMMARY_PROMPT = `You are a review processing summary writer. Your job is to:

1. Summarize the results from processing multiple reviews
2. Provide counts by category (bugs, features, praise)
3. Highlight key actions taken
4. Note any items pending human review

Format the summary in a clear, executive-friendly way.`;

export const summaryNode = async (state: typeof ReviewStateAnnotation.State) => {
  const bugResults = state.bug_results || [];
  const featureResults = state.feature_results || [];
  const praiseResults = state.praise_results || [];
  
  // Calculate feature approval statistics
  const totalFeatures = state.categorized_reviews?.features?.length || 0;
  const approvedFeatures = state.approved_feature_ids?.length || 0;
  const rejectedFeatures = totalFeatures - approvedFeatures;

  const stats = `
Bugs: ${bugResults.length}
Features: ${totalFeatures} (Approved: ${approvedFeatures}, Rejected: ${rejectedFeatures})
Praise: ${praiseResults.length}
`;

  const llm = new ChatOpenAI({ modelName: "gpt-5.2", temperature: 0 });

  const response = await llm.invoke([
    new SystemMessage(SUMMARY_PROMPT),
    new HumanMessage(`Statistics: ${stats}\n\nDetails:\nBugs: ${JSON.stringify(bugResults)}\nFeatures: ${totalFeatures} (Approved: ${approvedFeatures}, Rejected: ${rejectedFeatures}) - ${JSON.stringify(featureResults)}\nPraise: ${JSON.stringify(praiseResults)}`),
  ]);

  return {
    summary_report: response.content.toString(),
    messages: [response],
  };
};
