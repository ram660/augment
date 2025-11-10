# Backend Development Plan - Journey Integration

## Overview
Integrate the Journey Persistence Service into the chat workflow to enable persistent journey tracking, resume capability, and multimodal journey management.

---

## Phase 1: Journey Persistence Integration ✅ IN PROGRESS

### 1.1 Update Chat Workflow to Use Persistence Service

**Current State:**
- `_manage_journey()` uses in-memory `JourneyManager`
- No database persistence
- Journey state lost on restart

**Target State:**
- Use `JourneyPersistenceService` for all journey operations
- Persist journey state to database
- Enable resume from any point

**Implementation Steps:**

#### Step 1: Add JourneyPersistenceService to ChatWorkflow
- [ ] Import `JourneyPersistenceService` in `chat_workflow.py`
- [ ] Initialize service in `__init__` with database session
- [ ] Pass `db` parameter through workflow execution

#### Step 2: Update `_manage_journey()` Method
- [ ] Replace `self.journey_manager.start_journey()` with `await service.create_journey()`
- [ ] Replace `self.journey_manager.get_active_journey()` with `await service.get_user_journeys()`
- [ ] Replace `self.journey_manager.complete_step()` with `await service.update_step()`
- [ ] Add journey_id to conversation metadata

#### Step 3: Update `_save_conversation()` Method
- [ ] Save journey_id with conversation messages
- [ ] Link conversation to journey in database
- [ ] Update journey's last_activity_at timestamp

---

## Phase 2: Multimodal Journey Support

### 2.1 Image Upload Integration

**Features:**
- Upload images at any journey step
- Automatic image analysis
- Link images to specific steps
- Support before/after comparisons

**Implementation:**
- [ ] Add image upload endpoint to chat API
- [ ] Integrate with journey image service
- [ ] Add image analysis workflow
- [ ] Display images in chat timeline

### 2.2 Document Support

**Features:**
- Upload PDFs, contracts, quotes
- Extract text and metadata
- Link to journey steps
- Search within documents

**Implementation:**
- [ ] Add document upload endpoint
- [ ] PDF text extraction
- [ ] Document storage and indexing
- [ ] Document search integration

### 2.3 Web Search Integration

**Features:**
- Search for products, contractors, inspiration
- Save search results to journey
- Track research progress
- Generate recommendations

**Implementation:**
- [ ] Integrate web search API
- [ ] Save search results to journey
- [ ] Link results to steps
- [ ] Generate insights from searches

---

## Phase 3: Journey Analytics & Insights

### 3.1 Progress Tracking

**Metrics:**
- Time spent per step
- Completion rate
- Bottlenecks identification
- Estimated completion date

**Implementation:**
- [ ] Add analytics service
- [ ] Track step durations
- [ ] Calculate completion predictions
- [ ] Generate progress reports

### 3.2 Cost Tracking

**Features:**
- Budget vs actual tracking
- Cost breakdown by category
- Savings opportunities
- Contractor quote comparisons

**Implementation:**
- [ ] Add cost tracking to journey steps
- [ ] Integrate with product pricing
- [ ] Compare contractor quotes
- [ ] Generate cost reports

### 3.3 Decision History

**Features:**
- Track all decisions made
- Reasoning and alternatives
- Ability to revisit decisions
- Impact analysis

**Implementation:**
- [ ] Add decision tracking model
- [ ] Link decisions to steps
- [ ] Store alternatives and reasoning
- [ ] Enable decision rollback

---

## Phase 4: Advanced Journey Features

### 4.1 Journey Templates

**Features:**
- Create custom templates
- Share templates with community
- Template marketplace
- Template versioning

**Implementation:**
- [ ] Template CRUD API
- [ ] Template sharing system
- [ ] Template rating/reviews
- [ ] Template import/export

### 4.2 Collaboration

**Features:**
- Share journey with family/contractors
- Collaborative decision making
- Comments and feedback
- Task assignment

**Implementation:**
- [ ] Journey sharing API
- [ ] Permission management
- [ ] Comment system
- [ ] Task assignment

### 4.3 Journey Export

**Features:**
- Export to PDF
- Timeline visualization
- Cost summary
- Image gallery

**Implementation:**
- [ ] PDF generation service
- [ ] Timeline rendering
- [ ] Image compilation
- [ ] Export API endpoint

---

## Phase 5: Testing & Quality Assurance

### 5.1 Integration Tests

- [ ] Test journey creation from chat
- [ ] Test step progression
- [ ] Test image upload
- [ ] Test journey resume
- [ ] Test multi-user scenarios

### 5.2 Performance Tests

- [ ] Load test journey APIs
- [ ] Test concurrent journey updates
- [ ] Test large image uploads
- [ ] Test database query performance

### 5.3 End-to-End Tests

- [ ] Complete kitchen renovation journey
- [ ] Complete bathroom upgrade journey
- [ ] Test error recovery
- [ ] Test data consistency

---

## Implementation Priority

### High Priority (Week 1-2)
1. ✅ Journey Persistence Service (DONE)
2. ✅ Journey API Endpoints (DONE)
3. ✅ Journey Tests (DONE)
4. 🔄 Chat Workflow Integration (IN PROGRESS)
5. Image Upload Integration

### Medium Priority (Week 3-4)
6. Document Support
7. Progress Analytics
8. Cost Tracking
9. Journey Export

### Low Priority (Week 5+)
10. Custom Templates
11. Collaboration Features
12. Advanced Analytics

---

## Technical Considerations

### Database
- Use async SQLAlchemy for all operations
- Implement proper indexing for queries
- Use transactions for multi-step operations
- Implement soft deletes for journeys

### Caching
- Cache active journeys in Redis
- Cache journey templates
- Invalidate cache on updates
- Use cache-aside pattern

### Error Handling
- Graceful degradation if persistence fails
- Retry logic for transient errors
- Proper error messages to users
- Logging for debugging

### Security
- Validate user ownership of journeys
- Sanitize file uploads
- Rate limit API endpoints
- Encrypt sensitive data

---

## Success Metrics

### User Engagement
- % of users starting journeys
- Average journey completion rate
- Time to complete journeys
- User satisfaction scores

### Technical Performance
- API response times < 200ms
- Database query times < 50ms
- Image upload success rate > 99%
- Zero data loss incidents

### Business Impact
- Increased user retention
- Higher conversion rates
- More contractor connections
- Positive user feedback

---

## Next Steps

1. **Immediate**: Integrate JourneyPersistenceService into chat workflow
2. **This Week**: Add image upload to journey steps
3. **Next Week**: Implement progress analytics
4. **Month 1**: Complete multimodal support
5. **Month 2**: Launch collaboration features

