# Git Setup Guide for HomeView AI

This guide will help you set up and push your HomeView AI project to a Git repository.

## 📋 Prerequisites

- Git installed on your system ([Download Git](https://git-scm.com/downloads))
- A GitHub/GitLab/Bitbucket account
- Repository created on your Git hosting platform

## 🚀 Initial Setup

### 1. Initialize Git Repository (if not already done)

```bash
# Navigate to your project directory
cd c:\Users\ramma\Documents\augment-projects\augment

# Initialize git (if not already initialized)
git init

# Check git status
git status
```

### 2. Configure Git (First Time Only)

```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list
```

### 3. Review .gitignore

The `.gitignore` file is already configured to exclude:
- Python cache files (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- Database files (`*.db`, `*.sqlite`)
- Environment variables (`.env`)
- Credentials (`*-credentials.json`)
- Generated files (images, exports)
- Node modules
- IDE files

**Important**: Review `.gitignore` to ensure sensitive files are excluded!

### 4. Stage Your Files

```bash
# Add all files (respecting .gitignore)
git add .

# Or add specific files/directories
git add README.md
git add backend/
git add docs/

# Check what will be committed
git status
```

### 5. Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: HomeView AI v0.2.0

- Complete project structure
- Backend with FastAPI and LangChain
- Frontend with Next.js and React
- Digital twin visualization
- Image transformation with Gemini Imagen 3
- Comprehensive documentation
- Multi-floor plan support
- RAG system foundation"
```

## 🔗 Connect to Remote Repository

### Option 1: GitHub

```bash
# Add GitHub remote
git remote add origin https://github.com/yourusername/homeview-ai.git

# Or use SSH
git remote add origin git@github.com:yourusername/homeview-ai.git

# Verify remote
git remote -v
```

### Option 2: GitLab

```bash
# Add GitLab remote
git remote add origin https://gitlab.com/yourusername/homeview-ai.git

# Or use SSH
git remote add origin git@gitlab.com:yourusername/homeview-ai.git
```

### Option 3: Bitbucket

```bash
# Add Bitbucket remote
git remote add origin https://bitbucket.org/yourusername/homeview-ai.git

# Or use SSH
git remote add origin git@bitbucket.org:yourusername/homeview-ai.git
```

## 📤 Push to Remote

### First Push

```bash
# Push to main branch (creates it if doesn't exist)
git push -u origin main

# Or if your default branch is 'master'
git push -u origin master
```

### Subsequent Pushes

```bash
# After making changes
git add .
git commit -m "Your commit message"
git push
```

## 🌿 Branching Strategy

### Create a Development Branch

```bash
# Create and switch to dev branch
git checkout -b dev

# Push dev branch to remote
git push -u origin dev
```

### Feature Branch Workflow

```bash
# Create feature branch from dev
git checkout dev
git checkout -b feature/your-feature-name

# Make changes, commit
git add .
git commit -m "feat: add your feature"

# Push feature branch
git push -u origin feature/your-feature-name

# Merge back to dev (after review)
git checkout dev
git merge feature/your-feature-name
git push
```

## ✅ Pre-Push Checklist

Before pushing to Git, ensure:

- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] No credentials or API keys in code
- [ ] `homevision-credentials.json` is NOT committed
- [ ] Database files (`*.db`) are NOT committed
- [ ] `node_modules/` is NOT committed
- [ ] Generated images are NOT committed
- [ ] All sensitive data is excluded
- [ ] README.md is up to date
- [ ] CHANGELOG.md is updated
- [ ] Tests pass (run `pytest`)

## 🔒 Security Best Practices

### 1. Never Commit Secrets

```bash
# Check for accidentally staged secrets
git status

# Remove file from staging if needed
git reset HEAD .env
git reset HEAD homevision-credentials.json
```

### 2. Use Environment Variables

Always use `.env` file for:
- API keys (GOOGLE_API_KEY)
- Database credentials
- Storage credentials
- Secret keys

### 3. Review Before Pushing

```bash
# See what will be pushed
git diff origin/main

# Review commit history
git log --oneline -10
```

## 🔄 Common Git Commands

### Status and Information

```bash
# Check status
git status

# View commit history
git log --oneline

# View changes
git diff

# View remote repositories
git remote -v
```

### Making Changes

```bash
# Stage all changes
git add .

# Stage specific file
git add path/to/file

# Commit changes
git commit -m "Your message"

# Amend last commit
git commit --amend
```

### Syncing

```bash
# Pull latest changes
git pull

# Push changes
git push

# Fetch without merging
git fetch
```

### Branching

```bash
# List branches
git branch

# Create branch
git branch branch-name

# Switch branch
git checkout branch-name

# Create and switch
git checkout -b branch-name

# Delete branch
git branch -d branch-name
```

## 🆘 Troubleshooting

### Accidentally Committed Secrets

```bash
# Remove file from last commit (before push)
git reset HEAD~1
git add .  # Re-add files (excluding secrets)
git commit -m "Your message"

# If already pushed - contact repository admin
# You may need to rotate credentials
```

### Large Files

```bash
# If you get errors about large files
# Add them to .gitignore
echo "large-file.zip" >> .gitignore
git rm --cached large-file.zip
git commit -m "Remove large file"
```

### Merge Conflicts

```bash
# Pull latest changes
git pull

# Resolve conflicts in files
# Look for <<<<<<, ======, >>>>>> markers

# After resolving
git add .
git commit -m "Resolve merge conflicts"
git push
```

## 📚 Additional Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🎯 Next Steps

After pushing to Git:

1. **Set up branch protection** on main/master branch
2. **Configure CI/CD** (GitHub Actions, GitLab CI, etc.)
3. **Add collaborators** if working in a team
4. **Create issues** for planned features
5. **Set up project board** for task management

---

**Remember**: Always review what you're committing and never commit sensitive information!

