# GitHub Actions Setup Guide

This repository uses GitHub Actions for automated testing and deployment.

## 🔄 Workflows

### 1. Test and Auto-Merge (`test-and-merge.yml`)

**Triggers:** Push to `dev` branch

**What it does:**
1. ✅ Runs all unit tests
2. 📊 Generates coverage report
3. 🔀 Creates PR from `dev` to `main`
4. ✨ Auto-merges if tests pass

### 2. Test Main (`test-main.yml`)

**Triggers:** 
- Push to `main` branch
- Pull requests to `main`

**What it does:**
1. ✅ Runs all unit tests
2. 📊 Generates coverage reports
3. 📤 Uploads coverage artifacts

## 🚀 Setup Instructions

### Optional: Create Labels (Recommended)

Create helpful labels for automated PRs:

```bash
# Using GitHub CLI
gh label create "automated" --color "0E8A16" --description "Automated by GitHub Actions"
gh label create "auto-merge" --color "1D76DB" --description "Ready for auto-merge"

# Or create via GitHub UI:
# Repository → Issues → Labels → New label
```

**Labels:**
- `automated` - Green (#0E8A16) - Marks automated PRs
- `auto-merge` - Blue (#1D76DB) - Indicates auto-merge enabled

*Note: Labels are optional. The workflow works without them.*

### Required: Repository Settings

1. **Enable Actions**
   - Go to: `Settings` → `Actions` → `General`
   - Enable: "Allow all actions and reusable workflows"

2. **Workflow Permissions**
   - Go to: `Settings` → `Actions` → `General` → `Workflow permissions`
   - Select: "Read and write permissions"
   - Check: ☑️ "Allow GitHub Actions to create and approve pull requests"
   
   **⚠️ If this option is greyed out:**
   
   **For Organization Repositories:**
   1. Go to **Organization Settings**: `https://github.com/organizations/YOUR_ORG/settings`
   2. Navigate to: `Actions` → `General`
   3. Scroll to: `Workflow permissions`
   4. Enable: ☑️ "Allow GitHub Actions to create and approve pull requests"
   5. Save, then return to repository settings
   
   **Alternative: Use Personal Access Token (PAT):**
   1. Create PAT: https://github.com/settings/tokens
   2. Select scopes: `repo`, `workflow`
   3. Add to repository secrets as `GH_PAT`
   4. Workflow will automatically use it (already configured)

### Optional: Branch Protection Rules

For automatic merging to work smoothly:

1. **Protect Main Branch**
   - Go to: `Settings` → `Branches` → `Add rule`
   - Branch name pattern: `main`
   - Configure:
     - ☑️ Require a pull request before merging
     - ☐ Require approvals (0) - *Allow auto-merge without approval*
     - ☑️ Require status checks to pass before merging
       - Add: `Run Tests`
     - ☐ Require conversation resolution before merging
     - ☑️ Do not allow bypassing the above settings

2. **Optional: Protect Dev Branch**
   - Branch name pattern: `dev`
   - Configure:
     - ☑️ Require status checks to pass before merging
       - Add: `Run Tests`

### Optional: Code Coverage Service (Not Configured)

The workflows currently show coverage in the console output only. If you want coverage badges and PR comments, you can configure Codecov:

**What is Codecov?**
- Shows test coverage as badges in README
- Comments on PRs with coverage changes
- Tracks coverage trends over time

**To add it (optional):**
1. Sign up at [codecov.io](https://codecov.io)
2. Connect your repository
3. Get your Codecov token
4. Add to repository secrets: `CODECOV_TOKEN`
5. Uncomment Codecov steps in workflows

**Current setup:** Coverage reports generated locally (HTML + terminal), which is sufficient for most projects.

## 🔧 Usage

### Development Workflow

```bash
# 1. Work on dev branch
git checkout dev
git pull origin dev

# 2. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 3. Push to dev
git push origin dev

# 4. Workflow automatically:
#    - Runs tests
#    - Creates PR to main
#    - Auto-merges if tests pass
```

### What Happens Automatically

```
Push to dev
    ↓
Run Tests (✅)
    ↓
Create PR: dev → main
    ↓
Auto-merge enabled
    ↓
Merged to main! 🎉
```

### If Tests Fail

```
Push to dev
    ↓
Run Tests (❌)
    ↓
Workflow stops
    ↓
Fix issues
    ↓
Push again
```

## 🔍 Monitoring

### View Workflow Runs

- Go to: `Actions` tab
- See all workflow runs and their status

### View Test Results

- Click on any workflow run
- Click on the job (e.g., "Run Tests")
- Expand steps to see details

### View Coverage Reports

- **Console Output**: See coverage in workflow logs
- **HTML Report**: Download from workflow artifacts (test-main.yml only)
- **Terminal**: Coverage shown during test run

## 📋 Workflow Status Badges

Add to your README to show build status:

```markdown
![Dev Branch Tests](https://github.com/YOUR_USERNAME/memAlpha/actions/workflows/test-and-merge.yml/badge.svg?branch=dev)
![Main Branch Tests](https://github.com/YOUR_USERNAME/memAlpha/actions/workflows/test-main.yml/badge.svg?branch=main)
```

Replace `YOUR_USERNAME` with your GitHub username or organization name.

## 🛠️ Customization

### Change Auto-Merge Strategy

Edit `.github/workflows/test-and-merge.yml`:

```yaml
# Current: Squash merge
gh pr merge --squash

# Options:
gh pr merge --merge     # Regular merge commit
gh pr merge --rebase    # Rebase and merge
```

### Add More Checks

Add to the `test` job:

```yaml
- name: Lint code
  run: |
    source .venv/bin/activate
    ruff check src/

- name: Type check
  run: |
    source .venv/bin/activate
    mypy src/
```

### Require Manual Approval

Remove auto-merge and require approval:

1. Edit `.github/workflows/test-and-merge.yml`
2. Remove the `auto-merge` job
3. Add branch protection: "Require approvals (1)"

### Notify on Success/Failure

Add to workflows:

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    text: "Tests failed on dev branch!"
```

## 🔒 Security Considerations

### Branch Protection

- ✅ **DO**: Require status checks
- ✅ **DO**: Protect main branch
- ⚠️ **CONSIDER**: Require manual approval for sensitive projects
- ❌ **DON'T**: Allow force push to main

### Permissions

- ✅ **DO**: Use minimal required permissions
- ✅ **DO**: Use `GITHUB_TOKEN` for automation
- ⚠️ **CONSIDER**: Use separate bot account for approvals
- ❌ **DON'T**: Use personal access tokens unless necessary

### Testing

- ✅ **DO**: Run comprehensive tests before merging
- ✅ **DO**: Include coverage checks
- ⚠️ **CONSIDER**: Add integration tests
- ❌ **DON'T**: Merge if tests fail

## 🐛 Troubleshooting

### "Allow GitHub Actions to create and approve pull requests" is Greyed Out

**Cause:** Organization-level policy restriction

**Solution 1 - Organization Settings (Recommended):**
1. You need **organization admin** access
2. Go to: `https://github.com/organizations/YOUR_ORG/settings/actions`
3. Scroll to: "Workflow permissions"
4. Enable: ☑️ "Allow GitHub Actions to create and approve pull requests"
5. Save and return to repository settings (should now be enabled)

**Solution 2 - Use Personal Access Token:**
1. Create PAT at: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: `memAlpha Auto-Merge`
   - Scopes: ☑️ `repo` + ☑️ `workflow`
   - Generate and copy token
2. Add to repo secrets:
   - Repository → Settings → Secrets → Actions
   - New secret: `GH_PAT` = your token
3. Workflow already configured to use it!

**Solution 3 - Simplified Workflow (Manual Approval):**
1. Rename `test-and-pr.yml.disabled` to `test-and-pr.yml`
2. Disable `test-and-merge.yml`
3. PRs will be created but require manual approval

### "Auto-merge is not allowed" or "Protected branch rules not configured"

**Cause:** Branch protection not configured (required for auto-merge feature)

**Solution 1 - Enable Branch Protection (Recommended):**
1. Go to: Repository → Settings → Branches
2. Click: "Add branch protection rule"
3. Configure:
   - Branch name pattern: `main`
   - ☑️ "Require a pull request before merging"
   - ☑️ "Require approvals": 0
   - ☑️ "Allow auto-merge"
4. Save

**Solution 2 - Direct Merge (Current Workflow Default):**
The workflow now automatically falls back to direct merge if branch protection isn't configured. This works without any additional setup!

**Note:** The workflow tries auto-merge first, then falls back to direct merge if it fails. Both methods work fine.

### "Branch protection rules not satisfied"

**Solution:** Either:
1. Add required status checks to branch protection
2. OR disable "Require status checks" in branch protection

### "Permission denied"

**Solution:** Check workflow permissions:
- Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"

### "PR already exists"

**Note:** This is normal! The workflow will update the existing PR.

### "could not add label: 'automated' not found"

**Cause:** Labels don't exist in the repository

**Solution:** Labels are now optional (workflow updated). To add them:

```bash
# Create labels using gh CLI
gh label create "automated" --color "0E8A16" --description "Automated by GitHub Actions"
gh label create "auto-merge" --color "1D76DB" --description "Ready for auto-merge"

# Or via UI: Repository → Issues → Labels → New label
```

The workflow will work fine without labels!

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Auto-merge PRs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request)

## 🎯 Best Practices

1. **Always work on dev branch**
   - Don't commit directly to main
   - Let CI/CD handle the merge

2. **Write good commit messages**
   - They'll appear in PR descriptions
   - Use conventional commits (feat:, fix:, docs:)

3. **Keep dev up to date**
   ```bash
   git checkout dev
   git pull origin main  # Sync with main
   git push origin dev
   ```

4. **Monitor workflow runs**
   - Check Actions tab after pushing
   - Fix failures immediately

5. **Review auto-created PRs**
   - Even if auto-merged, review what was merged
   - Good for audit trail

---

**Questions?** Check workflow files in `.github/workflows/` or open an issue!

