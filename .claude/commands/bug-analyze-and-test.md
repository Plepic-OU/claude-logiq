
Link: $ARGUMENTS
User provides you link to bug description, if they have not, then stop and ask for it.

# Preparation
Fetch the report from the link.

Create `/bugreports/issue-{issue-id}` directory, let's calls this `issueDir`.
Write the bug report `{issueDir}/report.md`

# Root cause analysis and test creation
Use root-cause-finder agent to analyze the bug report and identify the root cause of the issue.
Tell the agent to place all temporary files in the `issueDir` directory.
The test should still go to the test directory.

Make sure the report will contain the root cause found.


# Pull request creation
Create a new branch called `fix/{issue-id}-{short-title}` and commit all our changes there.
Push it and create a new pull request. Make sure to add link to the issue that was analysed.
