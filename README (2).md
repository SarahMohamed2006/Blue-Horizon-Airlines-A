# Agent / Client — Blue Horizon Airlines MCP

## شرح بالعربي (اقرأ ده الأول)

الملف ده هو **العميل (Agent)** اللي بيتكلم مع سيرفر MCP بتاع فريقك. هو مش
سيرفر ومش قاعدة بيانات — هو "الشخص" اللي بيتصل بالسيرفر، يسلم عليه
(handshake)، يسأله ايه اللي هو عارف يعمله، وبعدين يستخدم الأدوات دي.

### الملفات
- `client.py` — الكود الكامل. كل جزء متعلم بتعليق `# === CONCERN: ... ===`
  عشان تلاقي أي حاجة بسرعة وانت أو الدكتور بتراجعوا الكود.
- `requirements.txt` — المكتبات المطلوبة.

### إزاي تشغله
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...   # لو هتستخدم sampling
python client.py stdio            # وضع التطوير المحلي
python client.py http             # لما السيرفر ينتقل لـ Streamable HTTP
```

### اللي الكود ده بيثبته (كل الـ 8 concerns)
| Concern | فين في الكود |
|---|---|
| Capability negotiation | `check_capabilities()` بعد `session.initialize()` |
| Notifications | `message_handler()` — بيمسك `tools/list_changed` |
| Elicitation | `elicitation_callback()` — بيسأل إنسان حقيقي في التيرمنال |
| Sampling | `sampling_callback()` — بيشغل موديل Claude فعلي من جهة العميل |
| Resources | خطوة 2 في `run_demo()` — بيقرا `policy://crew-duty` |
| Prompts | خطوة 3 في `run_demo()` — بيجيب `delay_announcement` |
| Progress tracking | `progress_callback()` مع أداة `generate_ops_report` |
| Defensive tool design | خطوة 5 — بيتأكد الأول إن السيرفر بيدعم elicitation قبل ما ينادي أداة كتابة (`cancel_flight`) |

### مهم جداً — حالة الفريق دلوقتي
لما فتحت الملفات اللي بعتوها لقيت:
1. أسامي الملفات ملخبطة عن محتواها الحقيقي:
   - اللي اسمه `elicitation.py` فيه فعلياً الـ **database schema** (لازم يترحل لمجلد `db/schema.sql`)
   - اللي اسمه `main.py` فيه فعلياً **seed data** (لازم يترحل لـ `db/seed.sql`)
   - اللي اسمه `resources.py` فيه فعلياً كود الـ **elicitation confirmations** (ده اللي هو فعلياً `elicitation.py`)
   - اللي اسمه `tools.py` فيه فعلياً الـ **prompts** بس (`@mcp.prompt`) — مفيش فيه أي `@mcp.tool` حقيقي
   - اللي اسمه `notifications.py` فيه فعلياً الـ **resources** (`@mcp.resource`) — مفيش فيه أي كود بيبعت `tools/list_changed`
   - اللي اسمه `requirements.txt` فيه فعلياً كود تشغيل السيرفر (`start_server`)
   - `server.py` فاضي بالكامل

2. **الأدوات الحقيقية (`@mcp.tool`) لسه مش موجودة**: فيه دوال بتجهز رسائل
   التأكيد (`build_cancel_flight_confirmation` وغيرها) لكن مفيش أداة فعلية
   بتنادي `elicitation/create` وتستخدمها.
3. مفيش كود لسه بيبعت `notifications/tools/list_changed`.
4. مفيش استدعاء `sampling/createMessage` من السيرفر.
5. مفيش تتبع progress في أي أداة.

**ده مش مشكلة فيك** — الكود اللي عملتلك في `client.py` **مصمم يشتغل
سليم حتى لو الحاجات دي لسه ناقصة**: كل خطوة فيها `try/except` بترجع
رسالة واضحة "لسه مش جاهز" بدل ما البرنامج يقفل بالغلط. أول ما زمايلك
يكملوا الأدوات دي، نفس الكود هيشتغل معاهم من غير ما تغير حرف.

### اللي محتاج تقوله لزمايلك (بالعربي عشان تبعتلهم)
- محتاجين نعمل أداة حقيقية `cancel_flight` (وباقي الأدوات) بـ `@mcp.tool`
  تستدعي `ctx.elicit(...)` جوه الهاندلر مش بس تجهز رسالة.
- محتاجين حدث فعلي يغيّر الأدوات المتاحة (مثلاً دخول supervisor) ويبعت
  `await server.request_context.session.send_tool_list_changed()`.
- محتاجين أداة تقرير طويلة تستخدم `ctx.report_progress(...)` أثناء الشغل.
- محتاجين استدعاء `ctx.session.create_message(...)` (sampling) جوه أداة
  زي توليد إعلان التأخير، بدل ما الـ prompt يترجع للموديل بتاع العميل بس
  من غير استخدام فعلي.
