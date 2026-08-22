(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/app/dashboard/knowledge/page.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>KnowledgePage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/api.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$dashboard$2f$dashboard$2d$context$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/dashboard/dashboard-context.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function KnowledgePage() {
    _s();
    const { user } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$dashboard$2f$dashboard$2d$context$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useDashboard"])();
    const isAdmin = user?.role === "admin";
    const [docs, setDocs] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [results, setResults] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [query, setQuery] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [limit, setLimit] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(5);
    const [busy, setBusy] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    async function load() {
        try {
            setDocs(await __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["api"].knowledgeDocuments());
        } catch (e) {
            setError(e instanceof Error ? e.message : "Could not load knowledge documents.");
        }
    }
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "KnowledgePage.useEffect": ()=>{
            load();
        }
    }["KnowledgePage.useEffect"], []);
    async function search(event) {
        event.preventDefault();
        if (query.trim().length < 3) return;
        setBusy(true);
        setError("");
        try {
            const data = await __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["api"].knowledgeSearch(query.trim(), limit);
            setResults(data.results ?? []);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Knowledge search failed.");
        } finally{
            setBusy(false);
        }
    }
    async function upload(event) {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        setBusy(true);
        try {
            await __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["api"].uploadKnowledge(form);
            event.currentTarget.reset();
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Document upload failed.");
        } finally{
            setBusy(false);
        }
    }
    async function remove(id) {
        if (!confirm("Delete this document and all vector chunks?")) return;
        await __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["api"].deleteKnowledge(id);
        await load();
    }
    const chunks = docs.reduce((sum, doc)=>sum + (doc.chunk_count ?? 0), 0);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "page-stack",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "page-hero compact",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "eyebrow",
                            children: "▤ RAG KNOWLEDGE"
                        }, void 0, false, {
                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                            lineNumber: 27,
                            columnNumber: 49
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                            children: "Search by meaning, not just words."
                        }, void 0, false, {
                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                            lineNumber: 27,
                            columnNumber: 95
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "Technical EV charging knowledge is extracted, chunked, embedded and retrieved from PostgreSQL + pgvector."
                        }, void 0, false, {
                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                            lineNumber: 27,
                            columnNumber: 138
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/app/dashboard/knowledge/page.tsx",
                    lineNumber: 27,
                    columnNumber: 44
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                lineNumber: 27,
                columnNumber: 5
            }, this),
            error && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "form-error",
                children: error
            }, void 0, false, {
                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                lineNumber: 28,
                columnNumber: 15
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "metric-grid two",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                children: "Indexed documents"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 29,
                                columnNumber: 51
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                children: docs.length
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 29,
                                columnNumber: 81
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 29,
                        columnNumber: 42
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                children: "Vector chunks"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 29,
                                columnNumber: 130
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                children: chunks
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 29,
                                columnNumber: 156
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 29,
                        columnNumber: 121
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                lineNumber: 29,
                columnNumber: 5
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "split-grid",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "panel-head",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            children: "Semantic search"
                                        }, void 0, false, {
                                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                            lineNumber: 31,
                                            columnNumber: 63
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("b", {
                                            children: "Grounded retrieval"
                                        }, void 0, false, {
                                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                            lineNumber: 31,
                                            columnNumber: 91
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                    lineNumber: 31,
                                    columnNumber: 58
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 31,
                                columnNumber: 30
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                                className: "search-form",
                                onSubmit: search,
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                        value: query,
                                        onChange: (e)=>setQuery(e.target.value),
                                        placeholder: "e.g. charger cable becomes extremely hot"
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 31,
                                        columnNumber: 176
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                        type: "range",
                                        min: "1",
                                        max: "10",
                                        value: limit,
                                        onChange: (e)=>setLimit(Number(e.target.value))
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 31,
                                        columnNumber: 296
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        disabled: busy,
                                        children: busy ? "Searching…" : `Search top ${limit}`
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 31,
                                        columnNumber: 399
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 31,
                                columnNumber: 128
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "search-results",
                                children: results.map((result, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("b", {
                                                        children: [
                                                            index + 1,
                                                            ". ",
                                                            result.title ?? "Untitled"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                        lineNumber: 31,
                                                        columnNumber: 595
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        children: [
                                                            Math.round((result.similarity ?? 0) * 100),
                                                            "%"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                        lineNumber: 31,
                                                        columnNumber: 643
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 31,
                                                columnNumber: 590
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("small", {
                                                children: [
                                                    result.category,
                                                    " · ",
                                                    result.source
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 31,
                                                columnNumber: 707
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                children: result.content
                                            }, void 0, false, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 31,
                                                columnNumber: 757
                                            }, this)
                                        ]
                                    }, `${result.title}-${index}`, true, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 31,
                                        columnNumber: 548
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 31,
                                columnNumber: 484
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 31,
                        columnNumber: 7
                    }, this),
                    isAdmin ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "panel-head",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            children: "Upload document"
                                        }, void 0, false, {
                                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                            lineNumber: 32,
                                            columnNumber: 74
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("b", {
                                            children: "PDF · TXT · MD"
                                        }, void 0, false, {
                                            fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                            lineNumber: 32,
                                            columnNumber: 102
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                    lineNumber: 32,
                                    columnNumber: 69
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 32,
                                columnNumber: 41
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                                className: "upload-form",
                                onSubmit: upload,
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                        children: [
                                            "File",
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                name: "file",
                                                type: "file",
                                                accept: ".pdf,.txt,.md",
                                                required: true
                                            }, void 0, false, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 32,
                                                columnNumber: 194
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 32,
                                        columnNumber: 183
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                        children: [
                                            "Title",
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                name: "title",
                                                placeholder: "ABB Terra 54 Installation Manual"
                                            }, void 0, false, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 32,
                                                columnNumber: 278
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 32,
                                        columnNumber: 266
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                        children: [
                                            "Category",
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                name: "category",
                                                defaultValue: "manual"
                                            }, void 0, false, {
                                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                                lineNumber: 32,
                                                columnNumber: 369
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 32,
                                        columnNumber: 354
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        disabled: busy,
                                        children: "Upload and index →"
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 32,
                                        columnNumber: 423
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 32,
                                columnNumber: 135
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 32,
                        columnNumber: 18
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "panel locked-panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                children: "🔒"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 32,
                                columnNumber: 526
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                children: "Viewer access"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 32,
                                columnNumber: 541
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                children: "Upload and deletion are restricted to administrators."
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 32,
                                columnNumber: 563
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 32,
                        columnNumber: 490
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                lineNumber: 30,
                columnNumber: 5
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "document-grid",
                children: docs.map((doc)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "doc-icon",
                                children: "▤"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 34,
                                columnNumber: 81
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                        children: doc.title
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 34,
                                        columnNumber: 119
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            doc.category,
                                            " · ",
                                            doc.chunk_count,
                                            " chunks"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 34,
                                        columnNumber: 139
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("small", {
                                        children: doc.source_filename
                                    }, void 0, false, {
                                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                        lineNumber: 34,
                                        columnNumber: 187
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 34,
                                columnNumber: 114
                            }, this),
                            isAdmin && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>remove(doc.id),
                                children: "Delete"
                            }, void 0, false, {
                                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                                lineNumber: 34,
                                columnNumber: 241
                            }, this)
                        ]
                    }, doc.id, true, {
                        fileName: "[project]/app/dashboard/knowledge/page.tsx",
                        lineNumber: 34,
                        columnNumber: 59
                    }, this))
            }, void 0, false, {
                fileName: "[project]/app/dashboard/knowledge/page.tsx",
                lineNumber: 34,
                columnNumber: 5
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/dashboard/knowledge/page.tsx",
        lineNumber: 26,
        columnNumber: 10
    }, this);
}
_s(KnowledgePage, "F1igH85mhV7kYtNG1zXScm4j9t4=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$dashboard$2f$dashboard$2d$context$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useDashboard"]
    ];
});
_c = KnowledgePage;
var _c;
__turbopack_context__.k.register(_c, "KnowledgePage");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=app_dashboard_knowledge_page_tsx_2039je7._.js.map