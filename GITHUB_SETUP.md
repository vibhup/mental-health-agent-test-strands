# GitHub Repository Setup Instructions

## Step 1: Create Repository on GitHub

1. Go to [GitHub.com](https://github.com) and sign in with `vibhupareek@gmail.com`
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `mental-health-agent`
   - **Description**: `A compassionate AI agent for mental health support using AWS Strands Agents SDK and Claude Sonnet 4`
   - **Visibility**: Choose Public or Private (recommend Private for mental health applications)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

## Step 2: Connect Local Repository to GitHub

After creating the repository on GitHub, run these commands in your terminal:

```bash
cd /Users/vibhup/mental-health-agent

# Add the GitHub remote (replace 'vibhupareek' with your actual GitHub username if different)
git remote add origin https://github.com/vibhupareek/mental-health-agent.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

1. Go to your repository on GitHub: `https://github.com/vibhupareek/mental-health-agent`
2. You should see all the files:
   - `mental_health_agent.py` (main agent code)
   - `README.md` (documentation)
   - `requirements.txt` (dependencies)
   - `example_usage.py` (usage examples)
   - `.env.example` (configuration template)
   - `setup.py` (installation script)
   - `LICENSE` (MIT license)

## Step 4: Set Up Repository Settings (Optional)

1. Go to repository Settings
2. Under "General" → "Features":
   - Enable Issues (for bug reports)
   - Enable Discussions (for community support)
3. Under "Security":
   - Enable vulnerability alerts
   - Set up branch protection rules for main branch

## Step 5: Add Repository Topics

Add these topics to help others discover your repository:
- `mental-health`
- `ai-agent`
- `aws-bedrock`
- `strands-agents`
- `claude-4`
- `healthcare`
- `python`
- `aws`

## Alternative: Using GitHub CLI

If you have GitHub CLI installed:

```bash
cd /Users/vibhup/mental-health-agent

# Create repository on GitHub
gh repo create mental-health-agent --private --description "A compassionate AI agent for mental health support using AWS Strands Agents SDK and Claude Sonnet 4"

# Push code
git push -u origin main
```

## Next Steps

After setting up the repository:

1. **Configure AWS credentials** for the project
2. **Set up SES** for email notifications
3. **Test the agent** with example conversations
4. **Add collaborators** if working with a team
5. **Set up CI/CD** for automated testing (optional)

## Security Notes

- Never commit actual `.env` files with real credentials
- Use GitHub Secrets for sensitive configuration in CI/CD
- Consider making the repository private if handling sensitive data
- Review all code before pushing to ensure no credentials are exposed
