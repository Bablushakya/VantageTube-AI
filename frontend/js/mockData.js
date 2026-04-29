/* ============================================
   VantageTube AI – Mock / Dummy Data
   mockData.js
   ============================================ */

const MOCK = {

  /* --- Channel Info --- */
  channel: {
    name: "TechWithAlex",
    handle: "@techwithAlex",
    avatar: "TA",
    subscribers: "48.2K",
    totalViews: "2.1M",
    videoCount: 87,
    joinDate: "March 2021",
    country: "United States",
    niche: "Tech & Gadgets",
    description: "Weekly tech reviews, tutorials, and gadget unboxings. Helping you make smarter tech decisions.",
    verified: false,
    growth: "+12.4%",
  },

  /* --- Channel Stats --- */
  stats: {
    subscribers:    { value: "48.2K",  change: "+1.2K",  trend: "up",   icon: "👥" },
    totalViews:     { value: "2.1M",   change: "+84K",   trend: "up",   icon: "👁️" },
    avgSeoScore:    { value: "67/100", change: "+5pts",  trend: "up",   icon: "📊" },
    videosAnalyzed: { value: "87",     change: "12 new", trend: "up",   icon: "🎬" },
  },

  /* --- Videos List --- */
  videos: [
    {
      id: "v001",
      title: "Top 10 Budget Laptops Under $500 in 2024",
      views: "142K",
      likes: "8.4K",
      comments: "312",
      duration: "14:32",
      publishedAt: "2 days ago",
      seoScore: 82,
      thumbnail: "💻",
      tags: ["budget laptops", "laptops 2024", "best laptops"],
    },
    {
      id: "v002",
      title: "iPhone 16 vs Samsung S24 – Full Comparison",
      views: "98K",
      likes: "5.1K",
      comments: "891",
      duration: "18:45",
      publishedAt: "1 week ago",
      seoScore: 74,
      thumbnail: "📱",
      tags: ["iphone 16", "samsung s24", "phone comparison"],
    },
    {
      id: "v003",
      title: "How I Set Up My Home Office for Under $300",
      views: "67K",
      likes: "4.2K",
      comments: "204",
      duration: "11:20",
      publishedAt: "2 weeks ago",
      seoScore: 58,
      thumbnail: "🖥️",
      tags: ["home office", "desk setup"],
    },
    {
      id: "v004",
      title: "Best Wireless Earbuds 2024 – Ranked!",
      views: "211K",
      likes: "12.3K",
      comments: "567",
      duration: "16:08",
      publishedAt: "3 weeks ago",
      seoScore: 91,
      thumbnail: "🎧",
      tags: ["wireless earbuds", "best earbuds 2024", "airpods alternative"],
    },
    {
      id: "v005",
      title: "My Honest Review of the M3 MacBook Pro",
      views: "54K",
      likes: "3.8K",
      comments: "178",
      duration: "22:15",
      publishedAt: "1 month ago",
      seoScore: 63,
      thumbnail: "💻",
      tags: ["macbook pro", "m3 chip", "apple review"],
    },
    {
      id: "v006",
      title: "5 Chrome Extensions Every Developer Needs",
      views: "38K",
      likes: "2.9K",
      comments: "143",
      duration: "9:44",
      publishedAt: "1 month ago",
      seoScore: 45,
      thumbnail: "🔧",
      tags: ["chrome extensions", "developer tools"],
    },
  ],

  /* --- SEO Analysis for a video --- */
  seoAnalysis: {
    v001: {
      score: 82,
      grade: "Good",
      criteria: [
        { name: "Title Optimization",    score: 90, status: "good",    detail: "Title has target keyword, good length (52 chars)" },
        { name: "Description Quality",   score: 78, status: "good",    detail: "Description is 280 chars, could be longer (300+)" },
        { name: "Tags Relevance",        score: 85, status: "good",    detail: "8 relevant tags found, mix of broad and specific" },
        { name: "Keyword Density",       score: 72, status: "warn",    detail: "Primary keyword appears 3x, aim for 5-7x" },
        { name: "Thumbnail Text",        score: 80, status: "good",    detail: "Clear text overlay detected" },
        { name: "Video Length",          score: 88, status: "good",    detail: "14 min is ideal for tutorial content" },
        { name: "Engagement Rate",       score: 76, status: "warn",    detail: "5.9% engagement, industry avg is 6.5%" },
        { name: "Call to Action",        score: 60, status: "warn",    detail: "No clear CTA found in description" },
      ],
      suggestions: [
        { type: "warn", title: "Add a Call to Action",       text: "Include 'Subscribe for more tech reviews' in your description to boost subscriber conversion." },
        { type: "warn", title: "Increase Keyword Density",   text: "Use 'budget laptops' 2-3 more times naturally in your description." },
        { type: "bad",  title: "Missing Timestamps",         text: "Add chapter timestamps to improve watch time and user experience." },
        { type: "good", title: "Great Title Structure",      text: "Your title follows the 'Number + Topic + Year' formula which performs well." },
      ],
    },
    v003: {
      score: 58,
      grade: "Average",
      criteria: [
        { name: "Title Optimization",    score: 55, status: "warn",    detail: "Title lacks primary keyword, too short (42 chars)" },
        { name: "Description Quality",   score: 40, status: "bad",     detail: "Description is only 95 chars, needs 300+" },
        { name: "Tags Relevance",        score: 65, status: "warn",    detail: "Only 4 tags, recommend 10-15 tags" },
        { name: "Keyword Density",       score: 50, status: "warn",    detail: "Primary keyword appears only 1x" },
        { name: "Thumbnail Text",        score: 70, status: "warn",    detail: "Text is small and hard to read on mobile" },
        { name: "Video Length",          score: 75, status: "good",    detail: "11 min is good for this content type" },
        { name: "Engagement Rate",       score: 62, status: "warn",    detail: "6.3% engagement, slightly below average" },
        { name: "Call to Action",        score: 30, status: "bad",     detail: "No CTA found in title, description, or tags" },
      ],
      suggestions: [
        { type: "bad",  title: "Rewrite Your Description",   text: "Your description is too short. Write at least 300 words with keywords naturally included." },
        { type: "bad",  title: "Add More Tags",              text: "You only have 4 tags. Add 10-15 relevant tags including long-tail keywords." },
        { type: "warn", title: "Improve Your Title",         text: "Consider: 'Budget Home Office Setup Under $300 – Full Guide 2024'" },
        { type: "warn", title: "Add Timestamps",             text: "Add chapter markers to improve viewer retention and SEO." },
      ],
    },
  },

  /* --- AI Generated Content --- */
  aiGenerated: {
    titles: [
      "Top 10 Budget Laptops Under $500 That Are Actually Worth Buying in 2024",
      "Best Cheap Laptops 2024: $500 Budget Picks That Outperform Expensive Ones",
      "I Tested 20 Budget Laptops – Here Are the Only 10 Worth Your Money (2024)",
    ],
    descriptions: [
      `Are you looking for the best budget laptops under $500 in 2024? In this video, I've tested and ranked the top 10 affordable laptops that deliver incredible performance without breaking the bank.

🔥 What You'll Learn:
• Best budget laptops for students and professionals
• Performance benchmarks and real-world tests
• Which laptops to avoid (and why)
• My top pick for every use case

⏱️ Timestamps:
0:00 – Introduction
1:30 – What to look for in a budget laptop
3:45 – #10 to #6 Ranked
8:20 – Top 5 Budget Laptops
12:00 – My #1 Pick & Final Verdict

💻 Laptops Reviewed: [List them here]

👍 If this helped you, LIKE and SUBSCRIBE for weekly tech reviews!
📩 Business inquiries: contact@techwithAlex.com

#BudgetLaptops #LaptopsUnder500 #BestLaptops2024 #TechReview`,
    ],
    tags: [
      "budget laptops 2024", "best laptops under 500", "cheap laptops",
      "laptop review", "best budget laptop", "student laptop",
      "affordable laptop", "laptop buying guide", "laptops 2024",
      "best laptop for students", "budget tech", "laptop comparison",
      "windows laptop", "chromebook alternative", "tech review 2024",
    ],
  },

  /* --- Trending Topics --- */
  trending: [
    {
      id: "t001",
      topic: "AI Laptops & Copilot+ PCs",
      niche: "Tech & Gadgets",
      description: "Microsoft's Copilot+ PC initiative is driving massive search interest. Creators covering AI-powered laptops are seeing 3x normal views.",
      viralScore: 94,
      searchVolume: "2.4M/mo",
      competition: "Medium",
      trend: "🔥 Exploding",
      tags: ["copilot+ pc", "ai laptop", "snapdragon x elite"],
      ideas: ["Best Copilot+ PCs Ranked", "Is AI in Laptops Actually Useful?"],
    },
    {
      id: "t002",
      topic: "Budget Smartphone Cameras 2024",
      niche: "Tech & Gadgets",
      description: "Mid-range phones are closing the gap with flagships. Camera comparison videos in this space are getting massive organic reach.",
      viralScore: 87,
      searchVolume: "1.8M/mo",
      competition: "High",
      trend: "📈 Rising",
      tags: ["budget phone camera", "mid range smartphone", "camera test"],
      ideas: ["$300 Phone vs $1200 Phone Camera Test", "Best Budget Camera Phone 2024"],
    },
    {
      id: "t003",
      topic: "Mechanical Keyboard Builds",
      niche: "Tech & Gadgets",
      description: "Custom keyboard building is a growing hobby. Tutorial and build log videos consistently hit 100K+ views in this niche.",
      viralScore: 79,
      searchVolume: "890K/mo",
      competition: "Low",
      trend: "📈 Rising",
      tags: ["mechanical keyboard", "custom keyboard build", "keyboard switches"],
      ideas: ["Building My Dream Keyboard Under $150", "Best Switches for Typing vs Gaming"],
    },
    {
      id: "t004",
      topic: "Home Server & NAS Setup",
      niche: "Tech & Gadgets",
      description: "Self-hosting and data privacy are trending. NAS and home server setup guides are seeing consistent growth with high watch time.",
      viralScore: 72,
      searchVolume: "620K/mo",
      competition: "Low",
      trend: "🌱 Growing",
      tags: ["home server", "nas setup", "self hosting", "proxmox"],
      ideas: ["Build a Home Server for $200", "Why I Stopped Using Cloud Storage"],
    },
    {
      id: "t005",
      topic: "Portable Monitors for Productivity",
      niche: "Tech & Gadgets",
      description: "Remote work and travel setups are driving demand for portable monitor reviews. Low competition with high buyer intent.",
      viralScore: 68,
      searchVolume: "480K/mo",
      competition: "Low",
      trend: "🌱 Growing",
      tags: ["portable monitor", "travel setup", "dual monitor laptop"],
      ideas: ["Best Portable Monitors 2024 – Ranked", "My Travel Work Setup Tour"],
    },
    {
      id: "t006",
      topic: "USB-C Hub & Dock Reviews",
      niche: "Tech & Gadgets",
      description: "As more laptops drop ports, USB-C hub reviews are evergreen content with strong affiliate potential and consistent search traffic.",
      viralScore: 61,
      searchVolume: "340K/mo",
      competition: "Medium",
      trend: "📊 Stable",
      tags: ["usb-c hub", "laptop dock", "thunderbolt hub"],
      ideas: ["Best USB-C Hubs for MacBook 2024", "I Tested 10 USB-C Hubs – Here's the Truth"],
    },
  ],

  /* --- Activity Feed --- */
  activity: [
    { icon: "📊", color: "rgba(108,99,255,0.15)", text: "SEO analysis completed for <strong>Top 10 Budget Laptops</strong>", time: "2 minutes ago" },
    { icon: "✨", color: "rgba(255,101,132,0.15)", text: "AI generated 3 title suggestions for <strong>iPhone 16 vs S24</strong>", time: "1 hour ago" },
    { icon: "🔥", color: "rgba(245,158,11,0.15)",  text: "New trending topic detected: <strong>AI Laptops & Copilot+ PCs</strong>", time: "3 hours ago" },
    { icon: "📈", color: "rgba(16,185,129,0.15)",  text: "Your channel gained <strong>+342 subscribers</strong> this week", time: "1 day ago" },
    { icon: "🎬", color: "rgba(59,130,246,0.15)",  text: "Video <strong>Best Wireless Earbuds 2024</strong> hit 200K views", time: "2 days ago" },
  ],

};
