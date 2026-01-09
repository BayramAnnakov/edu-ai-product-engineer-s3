import { StateGraph, START, END } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { ReviewStateAnnotation } from "./state.ts";
import { triageNode } from "./nodes/triage.ts";
import { bugReporterNode } from "./nodes/bug_reporter.ts";
import { featureAnalystNode, featureApprovalNode } from "./nodes/feature_analyst.ts";
import { praiseLoggerNode } from "./nodes/praise_logger.ts";
import { summaryNode } from "./nodes/summary.ts";

// Router that determines which processing nodes to execute in parallel
const routeToProcessors = (state: typeof ReviewStateAnnotation.State) => {
  const routes: string[] = [];
  
  if (state.categorized_reviews.bugs.length > 0) {
    routes.push("bug_reporter");
  }
  if (state.categorized_reviews.features.length > 0) {
    routes.push("feature_analyst");
  }
  if (state.categorized_reviews.praise.length > 0) {
    routes.push("praise_logger");
  }
  
  // If no reviews to process, go directly to summary
  if (routes.length === 0) {
    routes.push("summary");
  }
  
  return routes;
};

// Synchronization node that waits for all parallel processors to complete
const syncNode = async (state: typeof ReviewStateAnnotation.State) => {
  // This is a pass-through node that just ensures all results are collected
  console.log("All processing complete, moving to summary...");
  return {};
};

export function createContentReviewSquad(checkpointer?: any) {
  const workflow = new StateGraph(ReviewStateAnnotation)
    .addNode("triage", triageNode)
    .addNode("bug_reporter", bugReporterNode)
    .addNode("feature_analyst", featureAnalystNode)
    .addNode("feature_approval", featureApprovalNode)
    .addNode("praise_logger", praiseLoggerNode)
    .addNode("sync", syncNode)
    .addNode("summary", summaryNode)

    // Start with triage to categorize all reviews
    .addEdge(START, "triage")
    
    // Route from triage to multiple processors in parallel
    .addConditionalEdges("triage", routeToProcessors, [
      "bug_reporter",
      "feature_analyst", 
      "praise_logger",
      "summary"
    ])
    
    // All parallel processors converge to sync node
    .addEdge("bug_reporter", "sync")
    .addEdge("praise_logger", "sync")
    
    // Feature path needs approval before sync
    .addEdge("feature_analyst", "feature_approval")
    .addEdge("feature_approval", "sync")
    
    // Sync to summary to end
    .addEdge("sync", "summary")
    .addEdge("summary", END);

  return workflow.compile({
    checkpointer: checkpointer || new MemorySaver(),
    interruptAfter: ["feature_analyst"],
  });
}
