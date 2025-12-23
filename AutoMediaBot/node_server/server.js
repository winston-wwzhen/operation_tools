const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const cheerio = require('cheerio');
const schedule = require('node-schedule');
const { OpenAI } = require('openai');
const { chromium } = require('playwright');

const app = express();
const PORT = 3000;

// === 全局状态与配置 ===
const CONFIG_FILE = path.join(__dirname, 'config.json');
const COOKIES_FILE = path.join(__dirname, 'xhs_cookies.json');

// 默认配置
let appConfig = {
    llmApiKey: "",
    llmBaseUrl: "https://api.openai.com/v1",
    llmModel: "gpt-4",
    wechatAppId: "",
    wechatSecret: "",
    topicLimit: 3,
    scheduleCron: "0 */4 * * *", // 每4小时
    autoRun: false
};

// 运行时状态
let runtimeState = {
    isRunning: false,
    lastRunTime: null,
    nextRunTime: null,
    logs: []
};

let scheduledJob = null;

// === 初始化 ===
// 加载配置
if (fs.existsSync(CONFIG_FILE)) {
    try {
        const savedConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
        appConfig = { ...appConfig, ...savedConfig };
    } catch (e) {
        console.error("加载配置文件失败", e);
    }
}

// === 工具函数 ===
function log(level, message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { id: Date.now(), time: timestamp, level, message };
    runtimeState.logs.unshift(logEntry);
    if (runtimeState.logs.length > 100) runtimeState.logs.pop(); // 保留最近100条
    console.log(`[${level.toUpperCase()}] ${message}`);
}

function saveConfig() {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(appConfig, null, 2));
}

// === 核心业务模块 ===

// 1. 爬虫模块
async function getWeiboHotSearch() {
    log('info', '正在抓取微博热搜...');
    try {
        const response = await axios.get('https://s.weibo.com/top/summary', {
            headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' }
        });
        const $ = cheerio.load(response.data);
        const items = [];
        
        $('td.td-02 a').each((i, el) => {
            if (i >= appConfig.topicLimit) return false;
            const title = $(el).text();
            const link = "https://s.weibo.com" + $(el).attr('href');
            if (!link.includes("javascript")) {
                items.push({ title, link });
            }
        });
        
        log('success', `抓取成功: 找到 ${items.length} 个热点`);
        return items;
    } catch (error) {
        log('error', `抓取微博失败: ${error.message}`);
        return [];
    }
}

// 2. AI 内容生成模块
async function generateContent(topic, platform) {
    if (!appConfig.llmApiKey) {
        log('error', '未配置 LLM API Key，跳过生成');
        return null;
    }

    log('info', `正在为 [${platform}] 生成内容: ${topic.title}`);
    
    const client = new OpenAI({
        apiKey: appConfig.llmApiKey,
        baseURL: appConfig.llmBaseUrl
    });

    let systemPrompt = "";
    if (platform === "wechat") {
        systemPrompt = "你是一个专业的公众号编辑。请根据提供的热点话题，写一篇深度、有观点的资讯类文章。格式要求：标题吸引人，正文分段清晰，语气正式但有亲和力，HTML格式输出(使用h2, p标签)，字数800字左右。";
    } else {
        systemPrompt = "你是一个小红书爆款博主。请根据提供的热点话题，写一篇吸引眼球的笔记。要求：标题包含emoji且极具点击欲，正文多使用emoji，语气活泼、情绪化，分点陈述，要在末尾加上相关tag。字数300字左右。";
    }

    try {
        const completion = await client.chat.completions.create({
            model: appConfig.llmModel,
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: `当前热点话题是：${topic.title}。请为此生成内容。` }
            ]
        });
        return completion.choices[0].message.content;
    } catch (error) {
        log('error', `AI生成失败: ${error.message}`);
        return null;
    }
}

// 3. 微信发布模块
async function publishToWeChat(title, content) {
    if (!appConfig.wechatAppId || !appConfig.wechatSecret) {
        log('warning', '微信配置不完整，跳过发布');
        return;
    }
    
    try {
        // 获取 Token
        const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appConfig.wechatAppId}&secret=${appConfig.wechatSecret}`;
        const tokenRes = await axios.get(tokenUrl);
        if (!tokenRes.data.access_token) throw new Error(JSON.stringify(tokenRes.data));
        
        const accessToken = tokenRes.data.access_token;
        
        // 上传草稿
        // 注意：真实环境需要 thumb_media_id，这里仅模拟请求结构
        log('info', '正在上传微信草稿 (模拟)...');
        // const draftUrl = `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${accessToken}`;
        // await axios.post(draftUrl, { ... });
        
        log('success', `微信草稿已就绪: ${title}`);
    } catch (error) {
        log('error', `微信发布失败: ${error.message}`);
    }
}

// 4. 小红书发布模块 (Playwright)
async function publishToXHS(title, content) {
    if (!fs.existsSync(COOKIES_FILE)) {
        log('error', '未找到小红书 Cookies，请先在控制台点击“登录小红书”');
        return;
    }

    log('info', '启动浏览器准备发布小红书...');
    let browser = null;
    try {
        browser = await chromium.launch({ headless: false }); // 必须非 headless 才能尽量避开风控
        const context = await browser.newContext();
        
        const cookies = JSON.parse(fs.readFileSync(COOKIES_FILE, 'utf8'));
        await context.addCookies(cookies);
        
        const page = await context.newPage();
        await page.goto('https://creator.xiaohongshu.com/publish/publish');
        
        try {
            await page.waitForSelector('text=发布笔记', { timeout: 10000 });
        } catch(e) {
            log('error', '小红书登录失效，请重新登录');
            return;
        }

        // 模拟填写逻辑...
        log('info', '正在模拟填写小红书内容...');
        const titleInput = page.locator("input[placeholder*='填写标题']");
        await titleInput.fill(title.substring(0, 20));
        
        // 实际发布需要图片，这里仅演示流程
        log('success', `小红书内容填写完毕 (模拟): ${title}`);
        await page.waitForTimeout(3000); // 展示一下
        
    } catch (error) {
        log('error', `小红书发布流程出错: ${error.message}`);
    } finally {
        if (browser) await browser.close();
    }
}

// === 流程控制 ===
async function runTask() {
    if (runtimeState.isRunning) return;
    runtimeState.isRunning = true;
    runtimeState.lastRunTime = new Date().toLocaleString();
    log('info', '>>> 开始执行自动化任务');

    try {
        // 1. 获取热点
        const topics = await getWeiboHotSearch();
        
        if (topics.length > 0) {
            const topTopic = topics[0]; // 演示取第一个
            
            // 2. 生成并发布
            const wxContent = await generateContent(topTopic, "wechat");
            if (wxContent) await publishToWeChat(topTopic.title, wxContent);
            
            const xhsContent = await generateContent(topTopic, "xhs");
            if (xhsContent) await publishToXHS(topTopic.title, xhsContent);
        } else {
            log('warning', '没有获取到热点数据');
        }
        
    } catch (error) {
        log('error', `任务执行异常: ${error.message}`);
    } finally {
        runtimeState.isRunning = false;
        log('info', '<<< 任务执行完毕');
    }
}

// === Express 服务器配置 ===
app.use(express.static(path.join(__dirname, 'public')));
app.use(bodyParser.json());

// API 路由
app.get('/api/status', (req, res) => {
    res.json({
        config: appConfig,
        state: {
            ...runtimeState,
            nextRunTime: scheduledJob ? scheduledJob.nextInvocation() : null
        }
    });
});

app.post('/api/config', (req, res) => {
    appConfig = { ...appConfig, ...req.body };
    saveConfig();
    
    // 重启调度器
    if (scheduledJob) scheduledJob.cancel();
    if (appConfig.autoRun) {
        scheduledJob = schedule.scheduleJob(appConfig.scheduleCron, runTask);
        log('info', `定时任务已更新: ${appConfig.scheduleCron}`);
    } else {
        scheduledJob = null;
        log('info', '定时任务已关闭');
    }
    
    res.json({ success: true });
});

app.post('/api/run-once', (req, res) => {
    runTask();
    res.json({ success: true, message: "任务已触发" });
});

app.post('/api/login-xhs', async (req, res) => {
    log('info', '正在打开浏览器进行小红书登录...');
    res.json({ success: true, message: "浏览器已启动，请在弹出的窗口中扫码" });
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.goto('https://www.xiaohongshu.com');
    
    // 等待用户手动关闭浏览器或长时间未操作
    context.on('close', async () => {
        // 没什么好做的，Cookies需要手动触发保存吗？
        // 更好的方式是监听特定URL或等待时间
    });

    // 监听直到用户登录成功跳转，或给予30秒时间
    log('info', '请在 60秒 内完成扫码登录...');
    setTimeout(async () => {
        const cookies = await context.cookies();
        fs.writeFileSync(COOKIES_FILE, JSON.stringify(cookies, null, 2));
        log('success', 'Cookies 已保存！');
        await browser.close();
    }, 60000);
});

// 启动服务
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
    log('info', '系统启动完成，等待指令');
});