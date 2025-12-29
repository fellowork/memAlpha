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

### Required: Repository Settings

1. **Enable Actions**
   - Go to: `Settings` → `Actions` → `General`
   - Enable: "Allow all actions and reusable workflows"

2. **Workflow Permissions**
   - Go to: `Settings` → `Actions` → `General` → `Workflow permissions`
   - Select: "Read and write permissions"
   - Check: ☑️ "Allow GitHub Actions to create and approve pull requests"

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

### Optional: Code Coverage (Codecov)

To see coverage reports in PRs:

1. Sign up at [codecov.io](https://codecov.io)
2. Connect your repository
3. Add secret: `Settings` → `Secrets and variables` → `Actions`
   - Name: `CODECOV_TOKEN`
   - Value: Your Codecov token

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

- Codecov (if configured): See coverage badge in PR
- Artifacts: Download coverage HTML reports from workflow

## 📋 Workflow Status Badges

Add to your README:

```markdown
![Tests](https://github.com/YOUR_USERNAME/memAlpha/actions/workflows/test-and-merge.yml/badge.svg)
![Main Tests](https://github.com/YOUR_USERNAME/memAlpha/actions/workflows/test-main.yml/badge.svg)
```

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

### "Auto-merge is not allowed"

**Solution:** Enable in repository settings:
- Settings → Actions → General
- ☑️ "Allow GitHub Actions to create and approve pull requests"

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

