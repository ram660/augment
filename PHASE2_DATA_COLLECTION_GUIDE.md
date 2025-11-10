# Phase 2: Data Collection Guide

**Status:** Ready to Begin 🚀  
**Duration:** 3-6 Weeks  
**Start Date:** November 8, 2025

---

## 🎯 Goals

### Primary Objectives

1. **Collect 1,000+ chat interactions** with implicit reward tracking
2. **Gather 200+ explicit feedback submissions** from users
3. **Achieve 20%+ feedback submission rate** (200/1000)
4. **Build diverse dataset** across all personas (homeowner, contractor, DIY)

### Success Criteria

- ✅ 1,000+ interactions tracked in LightningStore
- ✅ 200+ feedback submissions in database
- ✅ 20%+ of users provide feedback
- ✅ Reward distribution: 30% excellent (>0.8), 50% good (0.5-0.8), 20% poor (<0.5)
- ✅ Coverage across all intent types (cost_estimate, diy_plan, product_search, etc.)

---

## 📊 What's Being Tracked

### Automatic Tracking (Every Interaction)

Every chat message is automatically tracked with:

**Interaction Data:**
- User message (prompt)
- AI response
- Conversation ID
- Intent classification
- Home ID (if Digital Twin enabled)
- User persona (homeowner/contractor/DIY)

**Implicit Reward Calculation:**
- Intent confidence (0.0-1.0)
- Context utilization (used home data?)
- Response length appropriateness
- Suggested actions provided
- Execution time
- Error count

**Typical Implicit Rewards:**
- 0.7-0.8: Good response with context
- 0.5-0.6: Acceptable response
- 0.3-0.4: Poor response or errors

### User Feedback (Explicit Rewards)

Users can provide feedback via:

**Feedback Types:**
- 👍 Thumbs Up → 1.0 reward
- 👎 Thumbs Down → 0.0 reward
- ⭐⭐⭐⭐⭐ 5 Stars → 1.0 reward
- ⭐⭐⭐⭐ 4 Stars → 0.8 reward
- ⭐⭐⭐ 3 Stars → 0.5 reward
- ⭐⭐ 2 Stars → 0.3 reward
- ⭐ 1 Star → 0.0 reward
- 📋 Copy → 0.9 reward (useful!)
- 🔄 Regenerate → 0.2 reward (not satisfied)

**Bonuses:**
- +0.1 for intent match
- +0.05 for context usage

---

## 🚀 Getting Started

### 1. Start the Application

```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend
cd homeview-frontend
npm run dev
```

### 2. Access the Dashboard

Open the admin dashboard to monitor progress:

```
http://localhost:3000/admin/dashboard
```

**Dashboard Features:**
- Real-time interaction count
- Feedback submission rate
- Average reward scores
- Reward distribution (excellent/good/poor)
- Phase 2 progress bars
- Auto-refreshes every 30 seconds

### 3. Test the Feedback UI

1. Go to the chat interface: `http://localhost:3000/`
2. Ask a question (e.g., "How much to paint my living room?")
3. Look for feedback buttons below the AI response:
   - 👍 Thumbs Up
   - 👎 Thumbs Down
   - ⭐ Star Rating
   - 📋 Copy
4. Click a button to submit feedback
5. Check the dashboard to see the feedback recorded

---

## 📈 Monitoring Progress

### Daily Checks

**Check the dashboard daily for:**

1. **Interaction Count**
   - Target: ~50-100 interactions per day
   - Week 1: 350-700 interactions
   - Week 2: 700-1,400 interactions
   - Week 3+: 1,000+ interactions ✅

2. **Feedback Submission Rate**
   - Target: 20%+ of interactions
   - If below 15%: Encourage more feedback (add prompts, incentives)
   - If above 25%: Great! Users are engaged

3. **Average Reward Score**
   - Target: 0.6-0.8 (good quality)
   - If below 0.5: Review low-scoring interactions, identify issues
   - If above 0.8: Excellent! AI is performing well

4. **Reward Distribution**
   - Target: 30% excellent, 50% good, 20% poor
   - If too many poor (<0.5): Investigate common failure patterns
   - If too many excellent (>0.8): May need more challenging queries

### Weekly Reviews

**Every week, analyze:**

1. **Top Performing Intents**
   - Which intents have highest rewards?
   - Which intents need improvement?

2. **Common Failure Patterns**
   - What types of questions get thumbs down?
   - What errors occur most frequently?

3. **User Engagement**
   - Are users providing feedback?
   - Are they using suggested actions?

4. **Data Quality**
   - Is the dataset diverse (all personas, all intents)?
   - Are there any data gaps?

### API Endpoints for Monitoring

```bash
# Get dashboard summary
curl http://localhost:8000/api/v1/admin/dashboard

# Get Agent Lightning stats
curl http://localhost:8000/api/v1/admin/agent-lightning/stats

# Get feedback stats (last 7 days)
curl http://localhost:8000/api/v1/admin/feedback/stats?days=7

# Get recent feedback
curl http://localhost:8000/api/v1/admin/feedback/recent?limit=20
```

---

## 🎓 Best Practices

### Encourage Feedback

**Strategies to increase feedback submission rate:**

1. **Make it easy** - Feedback buttons are visible and one-click
2. **Ask at the right time** - After helpful responses
3. **Show value** - "Your feedback helps us improve!"
4. **Incentivize** (optional) - Gamification, badges, etc.
5. **Follow up** - If thumbs down, ask "What could be better?"

### Ensure Data Quality

**Tips for high-quality data:**

1. **Diverse queries** - Test all personas and intents
2. **Real scenarios** - Use realistic home improvement questions
3. **Edge cases** - Test unusual or complex requests
4. **Error handling** - See how AI handles unclear questions
5. **Context variations** - Test with/without Digital Twin

### Test Scenarios

**Run these test scenarios weekly:**

1. **Homeowner Persona**
   - "How much to renovate my kitchen?"
   - "What paint color for a small bedroom?"
   - "Find me a sofa that fits my living room"

2. **Contractor Persona**
   - "Create a material takeoff for a bathroom remodel"
   - "Draft a scope of work for kitchen demo"
   - "What permits needed for egress window?"

3. **DIY Persona**
   - "Create a DIY plan for painting my room"
   - "Step-by-step guide to install backsplash"
   - "What tools do I need for deck building?"

4. **Edge Cases**
   - Unclear questions: "I want to fix stuff"
   - Complex multi-part: "Renovate kitchen, find products, estimate cost, create DIY plan"
   - Out of scope: "What's the weather today?"

---

## 📊 Sample Data Collection Schedule

### Week 1: Foundation (Days 1-7)

**Goal:** 350-700 interactions, 70-140 feedback

**Activities:**
- Set up monitoring dashboard
- Test all feedback types
- Run test scenarios (all personas)
- Identify any issues with tracking
- Adjust feedback UI if needed

**Daily Target:** 50-100 interactions, 10-20 feedback

### Week 2-3: Ramp Up (Days 8-21)

**Goal:** 700-1,400 interactions, 140-280 feedback

**Activities:**
- Increase usage (invite beta testers)
- Monitor reward distribution
- Identify low-performing intents
- Document common issues
- Refine prompts if needed

**Daily Target:** 50-100 interactions, 10-20 feedback

### Week 4-6: Optimization (Days 22-42)

**Goal:** 1,000+ interactions, 200+ feedback ✅

**Activities:**
- Reach data collection goals
- Analyze dataset quality
- Prepare for Phase 3 training
- Document insights and patterns
- Plan training strategy

**Daily Target:** 30-50 interactions, 6-10 feedback

---

## 🔍 Troubleshooting

### Low Feedback Submission Rate (<15%)

**Solutions:**
- Add feedback prompts in UI
- Show "Was this helpful?" after responses
- Simplify feedback (just thumbs up/down)
- Add feedback reminder after 3 messages

### Low Average Reward (<0.5)

**Solutions:**
- Review low-scoring interactions
- Identify common failure patterns
- Improve system prompts
- Add more context to responses
- Fix bugs causing errors

### Tracking Not Working

**Check:**
1. Agent Lightning installed: `pip show agentlightning`
2. Database exists: `lightning.db` in project root
3. Backend logs: Look for tracking errors
4. API endpoint: Test `/api/v1/chat/feedback`

### Dashboard Not Loading

**Check:**
1. Backend running: `http://localhost:8000/docs`
2. Admin API registered: Check `backend/main.py`
3. Authentication: May need to log in first
4. Browser console: Check for errors

---

## 📝 Data Collection Checklist

### Setup ✅

- [x] Agent Lightning installed
- [x] Feedback UI integrated
- [x] Admin dashboard created
- [x] Monitoring endpoints working
- [x] Tests passing (17/17)

### Week 1

- [ ] Dashboard accessible
- [ ] Feedback buttons working
- [ ] 350+ interactions tracked
- [ ] 70+ feedback submissions
- [ ] All personas tested
- [ ] All intents tested

### Week 2-3

- [ ] 700+ interactions tracked
- [ ] 140+ feedback submissions
- [ ] 15%+ submission rate
- [ ] Reward distribution analyzed
- [ ] Issues documented

### Week 4-6

- [ ] 1,000+ interactions tracked ✅
- [ ] 200+ feedback submissions ✅
- [ ] 20%+ submission rate ✅
- [ ] Dataset quality verified
- [ ] Ready for Phase 3 training

---

## 🎉 Next Steps

Once Phase 2 goals are met:

1. **Analyze Dataset**
   - Review reward distribution
   - Identify high/low performing patterns
   - Document insights

2. **Prepare for Training**
   - Export dataset from LightningStore
   - Split into train/test sets (80/20)
   - Configure GRPO algorithm

3. **Phase 3: Training**
   - Train optimized chat agent
   - Evaluate on test set
   - Compare to baseline

4. **Phase 4: Deployment**
   - A/B test optimized agent
   - Monitor performance
   - Gradual rollout

---

## 📚 Resources

- [Agent Lightning Implementation Guide](./docs/AGENT_LIGHTNING_IMPLEMENTATION.md)
- [Phase 1 Completion Summary](./AGENT_LIGHTNING_PHASE1_COMPLETE.md)
- [Test Suite](./backend/tests/test_agent_lightning_integration.py)
- [Admin Dashboard](http://localhost:3000/admin/dashboard)

---

**Questions or Issues?** Check the implementation guide or run the tests to verify everything is working correctly!

