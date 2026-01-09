import "dotenv/config";
import { createContentReviewSquad } from "./graph.ts";
import { processFeatureApprovals } from "./human_approval.ts";
import type { Review } from "./state.ts";

const sampleReviews: Review[] = [
    {"id": 1, "text": "App crashes when I try to export PDF", "rating": 1},
    {"id": 2, "text": "Would love to see dark mode support!", "rating": 4},
    {"id": 3, "text": "Best app ever! Love the new features", "rating": 5},
    {"id": 4, "text": "Login button doesn't work on Safari", "rating": 2},
    {"id": 5, "text": "Please add multi-language support", "rating": 3},
];

async function main() {
  const squad = createContentReviewSquad();

  console.log(`\n=== Processing ${sampleReviews.length} Reviews ===\n`);

  // Single graph call with all reviews
  const initialState = {
    reviews: sampleReviews,
    messages: [],
  };

  let result = await squad.invoke(initialState, { 
    configurable: { thread_id: "bulk_review_session" } 
  });

  // Handle Human-in-the-loop for features
  if (result.pending_approval) {
    const featureReviews = result.categorized_reviews.features;
    
    // Process approvals based on raw reviews (no AI specs yet)
    const approvedIds = await processFeatureApprovals(featureReviews);
    
    // Update state with individual approvals
    await squad.updateState(
      { configurable: { thread_id: "bulk_review_session" } }, 
      { 
        approved: approvedIds.length > 0,
        approved_feature_ids: approvedIds,
        pending_approval: false 
      },
      "feature_analyst"
    );
    
    // Resume - AI specs will now be generated only for approved features
    result = await squad.invoke(null, { 
      configurable: { thread_id: "bulk_review_session" } 
    });
  }

  console.log("\n=== FINAL SUMMARY REPORT ===");
  console.log(result.summary_report);
  
  console.log("\n=== PROCESSING RESULTS ===");
  console.log(`Total Bugs: ${result.bug_results.length}`);
  
  // Show feature approval counters
  const totalFeatureRequests = result.categorized_reviews.features.length;
  const approvedCount = result.feature_results.length;
  const rejectedCount = totalFeatureRequests - approvedCount;
  console.log(`Total Features: ${totalFeatureRequests} (Approved: ${approvedCount}, Rejected: ${rejectedCount})`);
  
  console.log(`Total Praise: ${result.praise_results.length}`);
}

main().catch(console.error);
