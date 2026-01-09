import * as readline from "readline";
import type { Review } from "./state.ts";

/**
 * Helper function to prompt user for Y/N input
 */
function askQuestion(query: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(query, (answer) => {
      rl.close();
      resolve(answer.trim().toUpperCase());
    });
  });
}

/**
 * Displays a feature request and prompts the user for approval
 * Note: No AI spec shown yet - approval is based on the raw review
 */
async function reviewFeature(review: Review): Promise<boolean> {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`Feature Request #${review.id}`);
  console.log(`${"=".repeat(60)}`);
  console.log(`Review: "${review.text}"`);
  console.log(`Rating: ${review.rating}/5`);
  console.log(`\nDecide if this feature request should be analyzed further.`);

  let answer = "";
  while (answer !== "Y" && answer !== "N") {
    answer = await askQuestion("Approve for analysis? (Y/N): ");
    if (answer !== "Y" && answer !== "N") {
      console.log("Please enter Y or N");
    }
  }

  const approved = answer === "Y";
  if (approved) {
    console.log(`✓ Feature #${review.id} APPROVED for specification`);
  } else {
    console.log(`✗ Feature #${review.id} REJECTED`);
  }

  return approved;
}

/**
 * Processes human approval for all feature requests
 * Returns array of approved feature IDs
 * Note: Approval happens BEFORE AI spec generation to save costs
 */
export async function processFeatureApprovals(
  featureReviews: Review[]
): Promise<number[]> {
  console.log("\n=== Human Approval Required for Feature Requests ===");
  console.log(`Found ${featureReviews.length} feature request(s)\n`);
  console.log("Reviewing raw feature requests (AI specs will be generated only for approved features)...\n");

  const approvedIds: number[] = [];

  // Get approval for each feature request based on raw review
  for (const review of featureReviews) {
    const approved = await reviewFeature(review);

    if (approved) {
      approvedIds.push(review.id);
    }
  }

  // Display summary
  console.log(`\n${"=".repeat(60)}`);
  console.log(
    `Approval Summary: ${approvedIds.length}/${featureReviews.length} features approved for specification`
  );
  console.log(`${"=".repeat(60)}\n`);

  return approvedIds;
}
