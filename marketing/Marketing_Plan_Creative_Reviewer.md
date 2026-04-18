# Marketing Plan: Creative Reviewer

## Executive Summary

Creative Reviewer (ABCDs Detector) is an open-source, AI-powered platform that automates video ad evaluation against YouTube's ABCD framework and creative intelligence metrics. It replaces slow, expensive, inconsistent manual creative review with comprehensive AI-driven analysis in minutes. This plan outlines positioning, target audiences, channels, and tactics to drive adoption.

---

## Current State Assessment (Feb 2026)

The upstream repo (google-marketing-solutions/abcds-detector) has been live for 2 years with zero marketing effort.

### GitHub Baseline

- **57 stars** / **30 forks** — Organic growth only; no launch posts, no directory listings, no content marketing
- **5 contributors** — Almost entirely internal Google Marketing Solutions team
- **6 total issues** — 5 bug reports + 1 feature request ("Run as an API" — already built in your fork)
- **33 PRs** total, 1 formal release
- **3 external contributors** (donaldseaton, nnajdova-git, lawrenae) — community exists but tiny
- **Empty repo description and no homepage URL** — Major missed discoverability opportunity

### Activity Gaps

- Last upstream commit: **October 2025** (4-month gap)
- Commit peaks: July 2025 (16), June 2025 (12) — activity correlates with v2 launch
- No commits Nov 2025 – Feb 2026 — the project appears dormant to outsiders

### Competitive Advantage Already Built (Your Fork)

Your fork has significant unreleased features that the upstream lacks:

- **Web UI** with drag-and-drop upload and real-time SSE progress
- **FastAPI server** with full REST API (the #1 community-requested feature)
- **PDF/HTML report generation**
- **Creative Intelligence** module (persuasion tactics, narrative structure)
- **Performance predictions** (CPA risk, ROAS, fatigue, funnel strength)
- **Scene detection with keyframes** and volume analysis
- **Brand intelligence** automated research
- **Google OAuth + credits/billing system**
- **Share buttons** (Twitter/LinkedIn) for word-of-mouth

### Key Insight

57 stars with zero marketing = strong latent demand. The ABCD framework is well-known in the advertising industry. The gap is **discoverability**, not product-market fit. Every marketing tactic should focus on getting the product in front of people who already need this — they just don't know it exists.

---

## Product Positioning

### Value Proposition

**"AI-powered creative review in minutes, not hours."**

Creative Reviewer uses Google AI (Gemini 2.5 Pro + Video Intelligence API) to score video ads across 23+ ABCD features, predict performance metrics (CPA risk, ROAS tier, creative fatigue), and deliver actionable recommendations — at ~$0.10–$0.30 per video.

### Key Differentiators

- **Research-backed framework** — Built on YouTube's ABCD principles, proven to drive 30%+ performance lift
- **Full-stack AI analysis** — Combines Video Intelligence API annotations with Gemini LLM reasoning (hybrid approach) for 90-95% accuracy vs. human experts
- **Performance predictions** — Goes beyond compliance scoring to predict CPA risk, ROAS tier, creative fatigue, and funnel strength
- **Open source** — Fully transparent, self-hosted in your own GCP project, GDPR/CCPA compliant
- **Speed & cost** — 30s video analyzed in ~2 min for ~$0.10–$0.30; scales to thousands of videos
- **Multiple output formats** — JSON, HTML, PDF reports with confidence scores and evidence

---

## Target Audiences

### Primary Segments

**1. Performance Marketing Agencies**

- Pain: Manual creative QA is a bottleneck; inconsistent feedback across reviewers
- Value: Standardized, scalable pre-flight creative QA; data-backed client recommendations
- Decision makers: Creative Directors, Head of Paid Media, VP of Performance

**2. Brand Marketing Teams (Mid-to-Enterprise)**

- Pain: Large video libraries with no systematic quality assurance; inconsistent adherence to brand guidelines across campaigns
- Value: Audit entire video libraries; ensure creative consistency; train internal creators with objective feedback
- Decision makers: Brand Managers, VP Marketing, CMO

**3. Media Buyers & Programmatic Teams**

- Pain: No way to predict which creatives will perform before spending budget
- Value: Creative QA before launch; performance predictions; fatigue detection to know when to refresh
- Decision makers: Media Directors, Performance Managers

**4. YouTube/Video-First Creators & Studios**

- Pain: No structured feedback loop on creative quality
- Value: Instant, objective feedback on every cut; optimize for YouTube's algorithm preferences

### Secondary Segments

- **Ad tech platforms** wanting to embed automated creative scoring
- **Academic researchers** doing large-scale video advertising studies
- **Google Cloud partners** looking for AI/ML showcase projects

---

## Go-to-Market Strategy (All Free / Zero-Cost Tactics)

Every tactic below costs $0 beyond your time. No paid ads, no sponsorships, no paid tools.

### Phase 1: Launch & Awareness (Months 1–3)

**Goal:** Get Creative Reviewer in front of the right people and establish credibility.

#### Organic Social & Community Posting

- **LinkedIn launch post** — Adapt LAUNCH_POST.md into a compelling personal post. Tell the story: the problem, why you built it, what it does, link to GitHub. Tag relevant people and use hashtags (#VideoAds, #YouTubeMarketing, #AItools, #MarTech, #OpenSource).
- **LinkedIn article** — Longer-form "How I Built an AI That Reviews Video Ads in 2 Minutes" post. Publish natively on LinkedIn for algorithm boost.
- **Twitter/X thread** — "I built an open-source AI that scores your video ads against YouTube's ABCD framework. Here's what it found when I ran it on 50 ads 🧵" — share surprising findings, screenshots of reports, link to repo.
- **Reddit posts** — Share in r/advertising, r/PPC, r/digital_marketing, r/machinelearning, r/SideProject. Tailor the angle per subreddit (technical for ML, practical for PPC).
- **Hacker News** — "Show HN: AI-powered video ad reviewer using Gemini + Video Intelligence API" — lead with the technical architecture.
- **Indie Hackers** — Post a "launch" thread and a "building in public" narrative.

#### Product Directories (Free Listings)

- **Product Hunt** — Free to submit. Prepare a strong tagline, 4-5 screenshots, a GIF demo, and a maker comment explaining the backstory.
- **AlternativeTo** — List as an alternative to CreativeX, VidMob, and manual ABCD reviews.
- **DevHunt** — Free developer tool directory.
- **ToolFinder / There's An AI For That** — Free AI tool directories with high organic traffic.
- **Awesome Lists** — Submit PRs to awesome-python, awesome-machine-learning, awesome-marketing-tech GitHub lists.

#### GitHub Optimization (High Priority — Currently Broken)

The repo currently has **no description and no homepage URL** — this kills discoverability in GitHub search.

- **Immediate:** Set repo description ("AI-powered video ad scoring against YouTube's ABCD framework") and homepage URL
- Professional README with GIF/video demo, badges, quickstart, architecture diagram — current README is developer-focused colab instructions with no product narrative
- "Good first issue" labels to attract contributors
- GitHub Discussions enabled for Q&A
- GitHub Topics: ai, video-analysis, youtube, advertising, gemini, google-cloud
- CONTRIBUTING.md exists (Google CLA); CODE_OF_CONDUCT.md added ✅
- **Triage the 6 open issues** — Close stale bugs, respond to the "Run as an API" request (#31) pointing to the new web app/API
- **Merge Dependabot PR** (#39) to show the project is actively maintained

#### Content Creation (Free Platforms)

- **Demo video** — Record a 2-minute Loom or OBS screencast: upload video → watch real-time progress → review PDF report. Post to YouTube, LinkedIn, Twitter.
- **Blog posts on Medium/Dev.to/Hashnode** (all free):
    - "How YouTube's ABCD Framework Can 2x Your Ad Performance (And How to Automate It)"
    - "Building an AI Video Analyzer with Gemini 2.5 Pro and Python"
    - "I Ran 50 YouTube Ads Through an AI Reviewer — Here's What I Learned"
- **SEO-targeted posts** (publish on your own GitHub Pages site or free blog):
    - Target: "YouTube ABCD framework checker", "AI video ad analysis", "automated creative review", "video ad scoring API"

### Phase 2: Engagement & Community Building (Months 3–6)

**Goal:** Build a user community, generate social proof, and create a content flywheel.

#### "Ad of the Week" Series (Free Content Flywheel)

- Every week, run a well-known ad (Super Bowl spot, viral campaign, etc.) through Creative Reviewer
- Post the analysis as a LinkedIn post + Twitter thread with screenshots of the report
- Tag the brand and agency — they'll often engage or reshare
- This creates recurring, shareable content at zero cost and demonstrates the tool in action

#### Community Channels (Free)

- **Discord server** — Create a free community for users to share results, get help, request features
- **GitHub Discussions** — Already free; use for technical Q&A and feature requests
- **Subreddit** — Consider creating r/CreativeReviewer if the community grows

#### Agency Outreach & Pilot Program

- DM 10-20 agency creative directors on LinkedIn offering to run their ads through the tool for free
- Ask for a testimonial or case study in return
- Post before/after results (with permission) as social proof

#### Guest Content & Cross-Promotion

- **Podcast guesting** — Pitch yourself to marketing podcasts (Marketing Over Coffee, Everyone Hates Marketers, The PPC Show, Marketing School). Podcasts constantly need guests — it's free.
- **Guest blog posts** — Offer to write for Search Engine Journal, Social Media Examiner, AdEspresso blog, or agency blogs. Free exposure to their audience.
- **YouTube collaborations** — Reach out to YouTube marketing channels to demo the tool

#### Newsletter (Free Tools)

- Start a bi-weekly "Creative Intelligence Digest" on Substack (free) or Buttondown (free tier)
- Content: ABCD tips, ad analysis highlights, tool updates, industry trends
- Promote via LinkedIn/Twitter and cross-link from GitHub README

#### Webinars & Live Demos (Free)

- Host monthly 30-min live demos on YouTube Live, LinkedIn Live, or Twitter Spaces (all free)
- Topics: "Live: Scoring Super Bowl Ads with AI", "How to Use Creative Reviewer for Your Agency", "ABCD Framework Deep Dive"
- Record and repurpose as YouTube tutorials

#### Conference & Meetup Talks (Free)

- Submit CFPs (calls for papers) to free or low-cost events:
    - Local marketing meetups (Meetup.com)
    - PyCon lightning talks
    - Google Developer Groups (GDGs)
    - Virtual summits (many are free to speak at)
- Repurpose talks as blog posts and YouTube videos

### Phase 3: Scaling & Network Effects (Months 6–12)

**Goal:** Turn users into advocates and create self-sustaining growth.

#### Social Proof & Case Studies

- Compile 5+ case studies from pilot agencies and early users
- Format as LinkedIn posts, blog articles, and a "Case Studies" section in the README
- Include specific metrics: "Agency X improved their ABCD scores from 52% to 84% and saw 25% lower CPA"

#### Open Source Community Growth

- Recognize top contributors in release notes and README
- Create a "Contributors" page on GitHub
- Host quarterly "contributor spotlight" posts on social media
- Encourage users to write their own blog posts about using the tool

#### SEO Compounding

- By this point, early blog posts should be ranking. Double down on what's working.
- Interlink all content (GitHub README → blog → YouTube → newsletter)
- Answer questions on Stack Overflow, Quora, and Reddit related to video ad optimization

#### Word-of-Mouth Tactics

- Add a "Share your results" CTA in the tool's output (e.g., "Tweet your ABCD score")
- Create a "Powered by Creative Reviewer" badge for agencies to display
- Encourage users to post their reports with a branded hashtag (#CreativeReviewer)

#### Strategic Partnerships (Free)

- Reach out to Google Developer Advocates for potential co-promotion (open source + Google AI = natural fit)
- Connect with GCP partner agencies who may want to showcase the tool to their clients
- Collaborate with marketing educators/course creators who can feature the tool in their curriculum

---

## Content Marketing Calendar

### Recurring Content (All Free)

- **Weekly:** "Ad of the Week" analysis post (LinkedIn + Twitter)
- **Bi-weekly:** Newsletter issue (Substack/Buttondown)
- **Monthly:** Live demo/webinar (YouTube Live or Twitter Spaces)
- **Quarterly:** "State of Video Ad Creative Quality" report compiled from aggregated tool data

### Launch Week Content (Month 1)

- Day 1: LinkedIn launch post + Twitter thread
- Day 2: Product Hunt submission
- Day 3: Hacker News "Show HN" post
- Day 4: Reddit posts (r/PPC, r/advertising, r/machinelearning)
- Day 5: Medium/Dev.to technical blog post
- Day 6: Demo video on YouTube
- Day 7: Indie Hackers launch post

---

## Channel Strategy (All Free)

- **LinkedIn** (primary) — Personal posts, articles, "Ad of the Week" series, agency outreach DMs. Highest ROI for B2B marketing audience.
- **Twitter/X** — Threads, quick tips, engage in #PPCChat and #DigitalMarketing conversations. Good for developer and marketer crossover audience.
- **YouTube** — Demo videos, webinar recordings, tutorial series. Long-tail SEO value.
- **GitHub** — The product's home. Discussions, contributor engagement, professional README, Awesome List PRs.
- **Reddit** — Targeted subreddit posts, helpful comments in relevant threads (don't spam).
- **Substack/Newsletter** — Owned audience. Bi-weekly digest builds long-term engagement.
- **Podcasts** — Guest appearances on marketing and tech podcasts. Free, high-credibility exposure.

---

## Key Metrics & KPIs

Baseline as of Feb 2026: 57 stars, 30 forks, 5 contributors, 0 newsletter subscribers, 0 community members.

### Awareness (from 57 stars baseline)

- GitHub stars — Target: **150 in 3 months** (3x), **300 in 6 months** (5x), **500 in 12 months** (9x)
- GitHub forks — Target: **50 in 3 months** (from 30), **80 in 6 months**
- Social media impressions and engagement rate
- Blog post views and SEO rankings for target keywords
- Product Hunt upvotes and ranking (top 10 of the day = success)

### Adoption

- GitHub clones (currently unknown — need push access to track)
- Number of videos analyzed (if telemetry is opt-in)
- Web app signups (if hosted version is deployed)
- API calls per month

### Engagement

- Newsletter subscribers — Target: **100 in 3 months**, **300 in 6 months** (realistic for niche B2B)
- Discord/community members — Target: **50 in 3 months**
- Contributors — Target: **10 in 6 months** (from 5)
- Webinar/live demo attendance
- Inbound DMs and partnership inquiries

### Social Proof

- Number of case studies and testimonials (target: 3 in 6 months)
- User-generated content (blog posts, tweets, videos about the tool)
- Conference talk acceptances
- External contributor PRs (target: 5 in 6 months, from ~3 total to date)

---

## Competitive Positioning

- **vs. Manual Review:** 100x faster, perfectly consistent, available 24/7
- **vs. Generic AI tools (ChatGPT, etc.):** Purpose-built for video ads; structured ABCD scoring; performance predictions; annotation-backed accuracy
- **vs. Enterprise creative analytics (CreativeX, VidMob):** Open source and free; no vendor lock-in; self-hosted; transparent methodology; community-driven

---

## Risk Mitigation

- **"Dormant project" perception** — The 4-month commit gap (Nov 2025 – Feb 2026) makes the project look abandoned. Immediate priority: merge Dependabot PR, push your enhanced fork's features, and resume regular commit activity. Even small commits (docs, tests, refactors) signal active maintenance.
- **Fork vs. upstream tension** — Your fork has massive enhancements the upstream lacks. Decide whether to: (a) contribute back to the upstream and market from the google-marketing-solutions org, (b) launch your fork as a separate project, or (c) use upstream for OSS credibility but deploy your fork as the product. Option (a) is strongest for marketing leverage (Google org credibility).
- **LLM accuracy concerns** — Lead with hybrid approach (annotations + LLM); publish accuracy benchmarks; position as screening tool with human QA for critical decisions
- **GCP dependency** — Clearly communicate GCP requirement in all content; document setup thoroughly; explore multi-cloud on roadmap
- **Audience fatigue** — Vary content formats (posts, threads, videos, live demos, guest appearances); rotate "Ad of the Week" across industries
- **Open source sustainability** — Build community early; recognize contributors; consider GitHub Sponsors or OpenCollective if the project grows

---

## Immediate Action Items (This Week)

Highest-impact tasks to do right now, before any content marketing:

1. **Set GitHub repo description and homepage URL** — Takes 30 seconds, immediately improves search discoverability
2. **Triage all 6 open issues** — Close stale ones, reply to #31 with your API solution
3. **Merge Dependabot PR #39** — Shows the project is alive
4. **Push at least one meaningful commit** — Breaks the 4-month gap
5. **Add GitHub Topics** — ai, video-analysis, youtube, advertising, gemini, google-cloud, python
6. **Record 2-minute demo video** — Required for Product Hunt, LinkedIn, and Twitter launches
7. **Replace [LINK] placeholders** in all marketing/launch/ drafts with actual URLs
