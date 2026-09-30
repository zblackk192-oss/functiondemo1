// ============================================================
// AI辅助汽车系统功能逻辑分析 Demo
// app.js
// ============================================================


// ============================================================
// 全局状态
// ============================================================

const appState = {

    currentCase: null,

    currentFunctions: [],

    currentRelations: [],

    completionReady: false,

    completionResult: {

        functions: [],

        relations: []

    },

    llmResult: {

        functionUpdates: [],

        missingFunctions: [],

        missingRelations: []

    },

    functionDecisions: [],

    relationDecisions: [],

    finalResult: null

};


// ============================================================
// 页面加载
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    loadCurrentCase
);


// ============================================================
// 页面初始化
// ============================================================

async function loadCurrentCase() {


    try {

        const response =
            await fetch(
                "/api/current-case"
            );


        if (!response.ok) {

            throw new Error(
                "当前案例接口请求失败"
            );

        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "当前案例加载失败"
            );

        }


        const currentCase =
            data.case || {};


        appState.currentCase =
            currentCase;


        appState.currentFunctions =
            normalizeCurrentFunctions(
                currentCase
            );


        appState.currentRelations =
            Array.isArray(
                currentCase.relations
            )
                ? currentCase.relations
                : [];


        renderCurrentCase(
            currentCase
        );

    }

    catch (error) {

        console.error(
            "加载当前案例失败：",
            error
        );

        setSystemStatus(
            "当前案例加载失败",
            "error"
        );

    }

}


// ============================================================
// HTML安全转义
// ============================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


// ============================================================
// 数组格式化
// ============================================================

function formatArray(value) {

    if (!value) {

        return "";

    }


    if (Array.isArray(value)) {

        return value
            .filter(
                item =>
                    item !== null &&
                    item !== undefined &&
                    String(item).trim() !== ""
            )
            .join("、");

    }


    return String(value);

}


// ============================================================
// 当前案例标准化
// ============================================================

function normalizeCurrentFunctions(
    data
) {

    if (
        Array.isArray(
            data.functions
        )
    ) {

        return data.functions.map(
            function(item, index) {

                return normalizeFunction(
                    item,
                    index
                );

            }
        );

    }


    const functionPoints =
        Array.isArray(
            data.function_points
        )
            ? data.function_points
            : [];


    const events =
        Array.isArray(data.events)
            ? data.events
            : [];


    return functionPoints.map(
        function(point, index) {

            const event =
                events[index] || {};


            const name =
                typeof point === "string"
                    ? point
                    : (
                        point.name ||
                        point.functionName ||
                        point.function ||
                        event.name ||
                        event.action ||
                        ""
                    );


            return normalizeFunction(
                {

                    id:
                        event.id ||
                        (
                            typeof point === "object"
                                ? point.id
                                : ""
                        ) ||
                        `F${String(index + 1).padStart(3, "0")}`,

                    name: name,

                    action:
                        (
                            typeof point === "object"
                                ? point.action
                                : ""
                        ) ||
                        event.action ||
                        "",

                    object:
                        (
                            typeof point === "object"
                                ? point.object
                                : ""
                        ) ||
                        event.object ||
                        "",

                    effect:
                        (
                            typeof point === "object"
                                ? point.effect
                                : ""
                        ) ||
                        event.effect ||
                        "",

                    trigger:
                        (
                            typeof point === "object"
                                ? point.trigger
                                : ""
                        ) ||
                        event.trigger ||
                        "",

                    condition:
                        (
                            typeof point === "object"
                                ? point.condition
                                : ""
                        ) ||
                        event.condition ||
                        "",

                    inputs:
                        (
                            typeof point === "object"
                                ? (
                                    point.inputs ||
                                    point.input
                                )
                                : null
                        ) ||
                        event.inputs ||
                        event.input ||
                        [],

                    outputs:
                        (
                            typeof point === "object"
                                ? (
                                    point.outputs ||
                                    point.output
                                )
                                : null
                        ) ||
                        event.outputs ||
                        event.output ||
                        [],

                    preconditions:
                        (
                            typeof point === "object"
                                ? point.preconditions
                                : null
                        ) ||
                        event.preconditions ||
                        [],

                    postconditions:
                        (
                            typeof point === "object"
                                ? point.postconditions
                                : null
                        ) ||
                        event.postconditions ||
                        [],

                    scenario:
                        (
                            typeof point === "object"
                                ? point.scenario
                                : ""
                        ) ||
                        event.scenario ||
                        "",

                    constraint:
                        (
                            typeof point === "object"
                                ? point.constraint
                                : ""
                        ) ||
                        event.constraint ||
                        ""

                },
                index
            );

        }
    );

}


// ============================================================
// 单个功能标准化
// ============================================================

function normalizeFunction(
    item,
    index = 0
) {

    item =
        item && typeof item === "object"
            ? item
            : {};


    return {

        id:
            item.id ||
            item.functionId ||
            `F${String(index + 1).padStart(3, "0")}`,

        name:
            item.name ||
            "",

        actor:
            item.actor ||
            "",

        action:
            item.action ||
            "",

        object:
            item.object ||
            "",

        effect:
            item.effect ||
            "",

        trigger:
            item.trigger ||
            "",

        condition:
            item.condition ||
            "",

        inputs:
            Array.isArray(item.inputs)
                ? item.inputs
                : (
                    Array.isArray(item.input)
                        ? item.input
                        : []
                ),

        outputs:
            Array.isArray(item.outputs)
                ? item.outputs
                : (
                    Array.isArray(item.output)
                        ? item.output
                        : []
                ),

        preconditions:
            Array.isArray(item.preconditions)
                ? item.preconditions
                : [],

        postconditions:
            Array.isArray(item.postconditions)
                ? item.postconditions
                : [],

        scenario:
            item.scenario ||
            "",

        constraint:
            item.constraint ||
            "",

        requirementEvidence:
            item.requirementEvidence ||
            "",

        historyEvidence:
            Array.isArray(item.historyEvidence)
                ? item.historyEvidence
                : [],

        evidenceType:
            item.evidenceType ||
            "",

        fieldCompletionEvidence:
            Array.isArray(item.fieldCompletionEvidence)
                ? item.fieldCompletionEvidence
                : [],

        reason:
            item.reason ||
            "",

        confidence:
            Number(
                item.confidence || 0
            )

    };

}


// ============================================================
// 展示当前设计
// ============================================================

function renderCurrentCase(data) {

    const caseIdElement =
        document.getElementById(
            "caseId"
        );


    if (caseIdElement) {

        caseIdElement.innerText =
            data.caseId ||
            "CURRENT001";

    }


    const container =
        document.getElementById(
            "currentFunctions"
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    const functions =
        appState.currentFunctions;


    if (
        functions.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                当前设计暂未解析出功能点
            </div>
        `;

        return;

    }


    functions.forEach(
        function(item) {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "function-card current-function-card";


            div.innerHTML = `

                <div class="function-id">
                    ${escapeHtml(
                        item.id
                    )}
                </div>

                <div class="function-name">
                    ${escapeHtml(
                        item.name
                    )}
                </div>

                <div class="function-mini-info">

                    ${escapeHtml(
                        item.action
                    )}

                    ${escapeHtml(
                        item.object
                    )}

                </div>

            `;


            container.appendChild(
                div
            );

        }
    );

}


// ============================================================
// 开始AI补全
// ============================================================

async function runCompletion() {

    const button =
        document.getElementById(
            "runButton"
        );


    if (button) {

        button.disabled = true;

        button.innerText =
            "AI正在分析，请稍候...";

    }


    setSystemStatus(
        "AI正在分析",
        "running"
    );


    resetSteps();


    setStep(
        "step-rag",
        "active"
    );


    hideElement(
        "graphSection"
    );


    // 每次重新分析都清空上一轮确认状态，避免旧结果被误认为本轮结果。
    appState.completionReady = false;

    appState.completionResult = {
        functions: [],
        relations: []
    };

    appState.functionDecisions = [];

    appState.relationDecisions = [];

    const finalConfirmButton =
        document.getElementById(
            "finalConfirmButton"
        );

    if (finalConfirmButton) {

        finalConfirmButton.disabled = false;

        finalConfirmButton.innerText =
            "✓ 确认并发布最终模型";

    }


    let elapsedSeconds = 0;


    const progressTimer =
        setInterval(
            function() {

                elapsedSeconds += 1;

                setSystemStatus(
                    `AI正在分析，已等待 ${elapsedSeconds} 秒`,
                    "running"
                );

            },
            1000
        );


    const controller =
        new AbortController();


    const timeoutTimer =
        setTimeout(
            function() {

                controller.abort();

            },
            150000
        );


    try {

        const response =
            await fetch(
                "/api/completion",
                {
                    method: "POST",
                    cache: "no-store",
                    signal: controller.signal
                }
            );


        if (!response.ok) {

            const errorData =
                await response.json().catch(
                    function() {

                        return {};

                    }
                );

            throw new Error(
                errorData.detail ||
                errorData.message ||
                `服务器返回HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "AI分析失败"
            );

        }


        // ----------------------------------------------------
        // 保存AI结果
        // ----------------------------------------------------

        appState.llmResult = {

            functionUpdates:
                Array.isArray(
                    data.llm_result?.functionUpdates
                )
                    ? data.llm_result.functionUpdates
                    : [],

            missingFunctions:
                Array.isArray(
                    data.llm_result?.missingFunctions
                )
                    ? data.llm_result.missingFunctions
                    : [],

            missingRelations:
                Array.isArray(
                    data.llm_result?.missingRelations
                )
                    ? data.llm_result.missingRelations
                    : []

        };


        appState.completionResult = {

            functions:
                Array.isArray(
                    data.completion_result?.functions
                )
                    ? data.completion_result.functions
                    : [],

            relations:
                Array.isArray(
                    data.completion_result?.relations
                )
                    ? data.completion_result.relations
                    : []

        };


        // ----------------------------------------------------
        // 初始化人工决策状态
        // ----------------------------------------------------

        const functionUpdateDecisions =
            appState.llmResult.functionUpdates.map(
                function(update) {

                    const updatedFunction =
                        applyFunctionUpdates(
                            appState.currentFunctions,
                            [update]
                        ).find(
                            item =>
                                item.id === update.id
                        );


                    if (!updatedFunction) {

                        return null;

                    }


                    updatedFunction.reason =
                        update.reason || "";

                    updatedFunction.confidence =
                        Number(
                            update.confidence || 0
                        );


                    return {

                        status: "pending",

                        modified: false,

                        suggestionType:
                            "field_update",

                        function:
                            updatedFunction

                    };

                }
            ).filter(Boolean);


        const missingFunctionDecisions =
            appState.llmResult.missingFunctions.map(
                function(item) {

                    return {

                        status: "pending",

                        modified: false,

                        suggestionType:
                            "missing_function",

                        function:
                            normalizeFunction(
                                item
                            )

                    };

                }
            );


        // 字段补全建议和缺失功能建议必须在本作用域内立即写入全局状态。
        // 之后的渲染与人工确认都只读取appState.functionDecisions。
        appState.functionDecisions = [
            ...functionUpdateDecisions,
            ...missingFunctionDecisions
        ];


        appState.relationDecisions =
            appState.llmResult.missingRelations.map(
                function(item) {

                    return {

                        status: "pending",

                        modified: false,

                        relation:
                            normalizeRelation(
                                item
                            )

                    };

                }
            );


        // 只有完整响应已经保存后，才允许进入最终确认。
        appState.completionReady = true;


        // ----------------------------------------------------
        // 流程状态
        // ----------------------------------------------------

        setStep(
            "step-rag",
            "completed"
        );

        setStep(
            "step-prompt",
            "completed"
        );

        setStep(
            "step-qwen",
            "completed"
        );

        setStep(
            "step-confirm",
            "active"
        );


        // ----------------------------------------------------
        // 知识库API检索结果
        // ----------------------------------------------------

        renderRetrieval(
            data.retrieval || []
        );


        // ----------------------------------------------------
        // AI建议
        // ----------------------------------------------------

        renderCompletionSuggestions();


        updateStatistics(
            data
        );


        setSystemStatus(
            "AI建议已生成，等待人工确认",
            "waiting"
        );

    }

    catch (error) {

        console.error(
            "AI分析失败：",
            error
        );


        const errorMessage =
            error.name === "AbortError"
                ? "AI分析超过150秒，已停止等待；请检查后端日志中的Qwen调用状态"
                : error.message;


        alert(
            "AI分析失败：" +
            errorMessage
        );


        setSystemStatus(
            "AI分析失败",
            "error"
        );

    }

    finally {

        clearInterval(
            progressTimer
        );


        clearTimeout(
            timeoutTimer
        );

        if (button) {

            button.disabled = false;

            button.innerText =
                "重新进行AI辅助分析";

        }

    }

}


// ============================================================
// 重置流程状态
// ============================================================

function resetSteps() {

    [

        "step-rag",
        "step-prompt",
        "step-qwen",
        "step-confirm",
        "step-result"

    ].forEach(
        function(id) {

            setStep(
                id,
                ""
            );

        }
    );

}


// ============================================================
// 设置流程状态
// ============================================================

function setStep(
    id,
    state
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        return;

    }


    element.classList.remove(
        "active",
        "completed"
    );


    if (state) {

        element.classList.add(
            state
        );

    }

}


// ============================================================
// 设置系统状态
// ============================================================

function setSystemStatus(
    text,
    state
) {

    const dot =
        document.getElementById(
            "systemStatus"
        );


    const textElement =
        document.getElementById(
            "systemStatusText"
        );


    if (textElement) {

        textElement.innerText =
            text;

    }


    if (dot) {

        dot.classList.remove(
            "running",
            "waiting",
            "error"
        );


        if (state) {

            dot.classList.add(
                state
            );

        }

    }

}


// ============================================================
// 知识库API检索结果
// ============================================================

function renderRetrieval(
    retrieval
) {

    const section =
        document.getElementById(
            "retrievalSection"
        );


    const container =
        document.getElementById(
            "retrievalResults"
        );


    if (
        !section ||
        !container
    ) {

        return;

    }


    section.classList.remove(
        "hidden"
    );


    container.innerHTML = "";


    if (
        !Array.isArray(retrieval) ||
        retrieval.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                知识库未返回匹配子图
            </div>
        `;

        return;

    }


    retrieval.forEach(
        function(item, index) {

            const labels =
                item &&
                typeof item.labels === "object" &&
                item.labels !== null
                    ? item.labels
                    : {};


            const functions =
                formatArray(
                    labels.functions || []
                );


            const relations =
                formatArray(
                    labels.relations || []
                );


            const scenarios =
                formatArray(
                    item.scenarios || []
                );


            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "retrieval-item";


            const rank = Number(item.rank);


            const rankText =
                Number.isFinite(rank)
                    ? rank.toFixed(4)
                    : "-";


            div.innerHTML = `

                <div class="retrieval-header">

                    <div>

                        <span class="retrieval-rank">
                            Top-${index + 1}
                        </span>

                        <strong>

                            ${escapeHtml(
                                item.title ||
                                item.subgraph_id ||
                                "未命名知识子图"
                            )}

                        </strong>

                    </div>

                    <span class="score">

                        FTS5 rank
                        ${escapeHtml(rankText)}

                    </span>

                </div>


                <div class="retrieval-body">

                    <div>
                        <strong>
                            子图ID：
                        </strong>

                        ${escapeHtml(
                            item.subgraph_id || ""
                        )}
                    </div>

                    <div>
                        <strong>
                            案例：
                        </strong>

                        ${escapeHtml(
                            item.case_title || ""
                        )}
                    </div>

                    <div>
                        <strong>
                            视图：
                        </strong>

                        ${escapeHtml(
                            [
                                item.view_type || "",
                                item.view_title || ""
                            ].filter(Boolean).join(" / ")
                        )}
                    </div>

                    <div class="retrieval-source">

                        <strong>
                            描述：
                        </strong>

                        ${escapeHtml(
                            item.description || ""
                        )}

                    </div>

                    ${functions ? `
                        <div>
                            <strong>功能标签：</strong>
                            ${escapeHtml(functions)}
                        </div>
                    ` : ""}

                    ${relations ? `
                        <div>
                            <strong>关系标签：</strong>
                            ${escapeHtml(relations)}
                        </div>
                    ` : ""}

                    ${scenarios ? `
                        <div>
                            <strong>适用场景：</strong>
                            ${escapeHtml(scenarios)}
                        </div>
                    ` : ""}

                </div>

            `;


            container.appendChild(
                div
            );

        }
    );

}


// ============================================================
// AI建议总渲染
// ============================================================

function renderCompletionSuggestions() {

    const section =
        document.getElementById(
            "completionSection"
        );


    if (section) {

        section.classList.remove(
            "hidden"
        );

    }


    renderFunctionSuggestions();

    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 功能建议
// ============================================================

function renderFunctionSuggestions() {

    const container =
        document.getElementById(
            "completionResults"
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    const decisions =
        appState.functionDecisions;


    if (
        decisions.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                AI未发现需要补充的功能点。
            </div>
        `;

        return;

    }


    decisions.forEach(
        function(decision, index) {

            container.appendChild(
                createFunctionSuggestion(
                    decision,
                    index
                )
            );

        }
    );

}


// ============================================================
// 创建功能建议卡片
// ============================================================

function createFunctionSuggestion(
    decision,
    index
) {

    const functionData =
        decision.function;


    const div =
        document.createElement(
            "div"
        );


    div.className =
        `completion-item decision-${decision.status}`;


    const confidence =
        Math.round(
            Number(
                functionData.confidence || 0
            ) * 100
        );


    div.innerHTML = `

        <div class="decision-header">

            <div>

                <span class="suggestion-index">
                    ${
                        decision.suggestionType ===
                        "field_update"
                            ? "字段补全"
                            : "缺失功能"
                    }${index + 1}
                </span>

                <strong>

                    ${escapeHtml(
                        functionData.id
                    )}

                    ${escapeHtml(
                        functionData.name
                    )}

                </strong>

            </div>


            <span class="decision-badge">
                ${getDecisionText(
                    decision.status
                )}
            </span>

        </div>


        <div class="confidence-row">

            <span>
                AI置信度
            </span>

            <strong>
                ${confidence}%
            </strong>

        </div>


        <div class="reason">

            <strong>
                补全原因：
            </strong>

            ${escapeHtml(
                functionData.reason || ""
            )}

        </div>


        <div class="slot-grid">

            ${renderSlot(
                "Actor",
                functionData.actor
            )}

            ${renderSlot(
                "Action",
                functionData.action
            )}

            ${renderSlot(
                "Object",
                functionData.object
            )}

            ${renderSlot(
                "Effect",
                functionData.effect
            )}

            ${renderSlot(
                "Trigger",
                functionData.trigger
            )}

            ${renderSlot(
                "Condition",
                functionData.condition
            )}

            ${renderSlot(
                "Inputs",
                formatArray(
                    functionData.inputs
                )
            )}

            ${renderSlot(
                "Outputs",
                formatArray(
                    functionData.outputs
                )
            )}

            ${renderSlot(
                "Preconditions",
                formatArray(
                    functionData.preconditions
                )
            )}

            ${renderSlot(
                "Postconditions",
                formatArray(
                    functionData.postconditions
                )
            )}

            ${renderSlot(
                "Scenario",
                functionData.scenario
            )}

            ${renderSlot(
                "Constraint",
                functionData.constraint
            )}

        </div>


        <div class="decision-actions">

            <button
                class="decision-button accept"
                onclick="acceptFunction(${index})"
            >
                ✓ 接受
            </button>


            <button
                class="decision-button edit"
                onclick="editFunction(${index})"
            >
                ✎ 修改
            </button>


            <button
                class="decision-button reject"
                onclick="rejectFunction(${index})"
            >
                ✕ 拒绝
            </button>

        </div>

    `;


    return div;

}


// ============================================================
// 功能字段
// ============================================================

function renderSlot(
    label,
    value
) {

    return `

        <div class="slot">

            <strong>
                ${escapeHtml(label)}：
            </strong>

            <span>
                ${escapeHtml(
                    value || "未填写"
                )}
            </span>

        </div>

    `;

}


// ============================================================
// 接受功能
// ============================================================

function acceptFunction(
    index
) {

    if (
        !appState.functionDecisions[index]
    ) {

        return;

    }


    appState.functionDecisions[index].status =
        "accepted";


    renderFunctionSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 拒绝功能
// ============================================================

function rejectFunction(
    index
) {

    if (
        !appState.functionDecisions[index]
    ) {

        return;

    }


    appState.functionDecisions[index].status =
        "rejected";


    renderFunctionSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 修改功能
// ============================================================

function editFunction(
    index
) {

    const decision =
        appState.functionDecisions[index];


    if (!decision) {

        return;

    }


    const functionData =
        decision.function;


    const container =
        document.getElementById(
            "completionResults"
        );


    const cards =
        container.querySelectorAll(
            ".completion-item"
        );


    const card =
        cards[index];


    if (!card) {

        return;

    }


    card.innerHTML = `

        <div class="decision-header">

            <strong>
                修改AI补全建议
            </strong>

            <span class="decision-badge editing">
                编辑中
            </span>

        </div>


        <div class="edit-grid">

            ${createEditInput(
                "id",
                "功能ID",
                functionData.id
            )}

            ${createEditInput(
                "name",
                "功能名称",
                functionData.name
            )}

            ${createEditInput(
                "actor",
                "Actor",
                functionData.actor
            )}

            ${createEditInput(
                "action",
                "Action",
                functionData.action
            )}

            ${createEditInput(
                "object",
                "Object",
                functionData.object
            )}

            ${createEditInput(
                "effect",
                "Effect",
                functionData.effect
            )}

            ${createEditInput(
                "trigger",
                "Trigger",
                functionData.trigger
            )}

            ${createEditInput(
                "condition",
                "Condition",
                functionData.condition
            )}

            ${createEditInput(
                "inputs",
                "Inputs",
                formatArray(
                    functionData.inputs
                )
            )}

            ${createEditInput(
                "outputs",
                "Outputs",
                formatArray(
                    functionData.outputs
                )
            )}

            ${createEditInput(
                "preconditions",
                "Preconditions",
                formatArray(
                    functionData.preconditions
                )
            )}

            ${createEditInput(
                "postconditions",
                "Postconditions",
                formatArray(
                    functionData.postconditions
                )
            )}

            ${createEditInput(
                "scenario",
                "Scenario",
                functionData.scenario
            )}

            ${createEditInput(
                "constraint",
                "Constraint",
                functionData.constraint
            )}

        </div>


        <div class="decision-actions">

            <button
                class="decision-button accept"
                onclick="saveFunctionEdit(${index})"
            >
                ✓ 保存修改并接受
            </button>


            <button
                class="decision-button reject"
                onclick="rejectFunction(${index})"
            >
                ✕ 拒绝
            </button>

        </div>

    `;

}


// ============================================================
// 编辑输入框
// ============================================================

function createEditInput(
    field,
    label,
    value
) {

    return `

        <label class="edit-field">

            <span>
                ${escapeHtml(label)}
            </span>

            <input
                type="text"
                data-field="${escapeHtml(field)}"
                value="${escapeHtml(value || "")}"
            >

        </label>

    `;

}


// ============================================================
// 保存功能修改
// ============================================================

function saveFunctionEdit(
    index
) {

    const container =
        document.getElementById(
            "completionResults"
        );


    const card =
        container.querySelectorAll(
            ".completion-item"
        )[index];


    if (!card) {

        return;

    }


    const inputs =
        card.querySelectorAll(
            "input[data-field]"
        );


    const functionData =
        appState.functionDecisions[index].function;


    inputs.forEach(
        function(input) {

            const field =
                input.dataset.field;


            const value =
                input.value.trim();


            if (
                field === "inputs" ||
                field === "outputs" ||
                field === "preconditions" ||
                field === "postconditions"
            ) {

                functionData[field] =
                    value
                        ? value
                            .split(/[、,，]/)
                            .map(
                                item =>
                                    item.trim()
                            )
                            .filter(Boolean)
                        : [];

            }

            else {

                functionData[field] =
                    value;

            }

        }
    );


    appState.functionDecisions[index].status =
        "accepted";

    appState.functionDecisions[index].modified =
        true;


    renderFunctionSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 全部接受功能
// ============================================================

function acceptAllFunctions() {

    appState.functionDecisions.forEach(
        function(decision) {

            decision.status =
                "accepted";

        }
    );


    renderFunctionSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 全部拒绝功能
// ============================================================

function rejectAllFunctions() {

    appState.functionDecisions.forEach(
        function(decision) {

            decision.status =
                "rejected";

        }
    );


    renderFunctionSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 关系建议
// ============================================================

function renderRelationSuggestions() {

    const container =
        document.getElementById(
            "relationResults"
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    const decisions =
        appState.relationDecisions;


    if (
        decisions.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                AI未发现需要补充的功能关系。
            </div>
        `;

        return;

    }


    decisions.forEach(
        function(decision, index) {

            const relation =
                decision.relation;


            const div =
                document.createElement(
                    "div"
                );


            div.className =
                `relation-suggestion decision-${decision.status}`;


            div.innerHTML = `

                <div class="relation-suggestion-main">

                    <span class="relation-index">
                        建议${index + 1}
                    </span>


                    <strong>
                        ${escapeHtml(
                            relation.source
                        )}
                    </strong>


                    <span class="relation-arrow">
                        →
                    </span>


                    <strong>
                        ${escapeHtml(
                            relation.target
                        )}
                    </strong>


                    <span class="relation-type">
                        ${escapeHtml(
                            relation.relation_type
                        )}
                    </span>


                    <span class="flow-object">
                        ${escapeHtml(
                            relation.flowObject
                        )}
                    </span>

                </div>


                <div class="relation-reason">

                    ${escapeHtml(
                        relation.reason || ""
                    )}

                </div>


                <div class="decision-actions">

                    <button
                        class="decision-button accept"
                        onclick="acceptRelation(${index})"
                    >
                        ✓ 接受
                    </button>


                    <button
                        class="decision-button edit"
                        onclick="editRelation(${index})"
                    >
                        ✎ 修改
                    </button>


                    <button
                        class="decision-button reject"
                        onclick="rejectRelation(${index})"
                    >
                        ✕ 拒绝
                    </button>

                </div>

            `;


            container.appendChild(
                div
            );

        }
    );

}


// ============================================================
// 关系标准化
// ============================================================

function normalizeRelation(
    item
) {

    item =
        item && typeof item === "object"
            ? item
            : {};


    return {

        source:
            item.source ||
            "",

        target:
            item.target ||
            "",

        source_name:
            item.source_name ||
            "",

        target_name:
            item.target_name ||
            "",

        relation_type:
            item.relation_type ||
            item.type ||
            "dependency",

        direction:
            item.direction ||
            "source_to_target",

        flowObject:
            item.flowObject ||
            "",

        confidence:
            Number(
                item.confidence || 0
            ),

        evidence:
            item.evidence ||
            "",

        historyEvidence:
            Array.isArray(item.historyEvidence)
                ? item.historyEvidence
                : [],

        evidenceType:
            item.evidenceType ||
            "",

        reason:
            item.reason ||
            ""

    };

}


// ============================================================
// 接受关系
// ============================================================

function acceptRelation(
    index
) {

    if (
        !appState.relationDecisions[index]
    ) {

        return;

    }


    appState.relationDecisions[index].status =
        "accepted";


    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 拒绝关系
// ============================================================

function rejectRelation(
    index
) {

    if (
        !appState.relationDecisions[index]
    ) {

        return;

    }


    appState.relationDecisions[index].status =
        "rejected";


    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 修改关系
// ============================================================

function editRelation(
    index
) {

    const decision =
        appState.relationDecisions[index];


    if (!decision) {

        return;

    }


    const relation =
        decision.relation;


    const container =
        document.getElementById(
            "relationResults"
        );


    const cards =
        container.querySelectorAll(
            ".relation-suggestion"
        );


    const card =
        cards[index];


    if (!card) {

        return;

    }


    card.innerHTML = `

        <div class="relation-edit-grid">

            ${createEditInput(
                "source",
                "Source",
                relation.source
            )}

            ${createEditInput(
                "target",
                "Target",
                relation.target
            )}

            ${createEditInput(
                "relation_type",
                "Relation Type",
                relation.relation_type
            )}

            ${createEditInput(
                "flowObject",
                "Flow Object",
                relation.flowObject
            )}

        </div>


        <div class="decision-actions">

            <button
                class="decision-button accept"
                onclick="saveRelationEdit(${index})"
            >
                ✓ 保存修改并接受
            </button>


            <button
                class="decision-button reject"
                onclick="rejectRelation(${index})"
            >
                ✕ 拒绝
            </button>

        </div>

    `;

}


// ============================================================
// 保存关系修改
// ============================================================

function saveRelationEdit(
    index
) {

    const container =
        document.getElementById(
            "relationResults"
        );


    const card =
        container.querySelectorAll(
            ".relation-suggestion"
        )[index];


    if (!card) {

        return;

    }


    const inputs =
        card.querySelectorAll(
            "input[data-field]"
        );


    const relation =
        appState.relationDecisions[index].relation;


    inputs.forEach(
        function(input) {

            relation[
                input.dataset.field
            ] =
                input.value.trim();

        }
    );


    appState.relationDecisions[index].status =
        "accepted";

    appState.relationDecisions[index].modified =
        true;


    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 全部接受关系
// ============================================================

function acceptAllRelations() {

    appState.relationDecisions.forEach(
        function(decision) {

            decision.status =
                "accepted";

        }
    );


    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 全部拒绝关系
// ============================================================

function rejectAllRelations() {

    appState.relationDecisions.forEach(
        function(decision) {

            decision.status =
                "rejected";

        }
    );


    renderRelationSuggestions();

    updateConfirmationProgress();

}


// ============================================================
// 确认进度
// ============================================================

function updateConfirmationProgress() {

    const all =
        [
            ...appState.functionDecisions,
            ...appState.relationDecisions
        ];


    const total =
        all.length;


    const decided =
        all.filter(
            item =>
                item.status !== "pending"
        ).length;


    const accepted =
        all.filter(
            item =>
                item.status === "accepted"
        ).length;


    const element =
        document.getElementById(
            "confirmCount"
        );


    if (element) {

        element.innerText =
            `${decided} / ${total}`;

    }


    const status =
        document.getElementById(
            "confirmationStatus"
        );


    if (!status) {

        return;

    }


    status.className =
        "status-tag";


    if (
        total === 0
    ) {

        status.classList.add(
            "confirmed"
        );

        status.innerText =
            "无需补全";

        return;

    }


    if (
        decided < total
    ) {

        status.classList.add(
            "pending"
        );

        status.innerText =
            `待确认 ${total - decided} 项`;

    }

    else {

        status.classList.add(
            "confirmed"
        );

        status.innerText =
            `已完成 ${accepted} 项接受`;

    }

}


// ============================================================
// 应用已有功能的字段补全
// ============================================================

function isMissingFunctionValue(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return true;

    }


    if (
        typeof value === "string"
    ) {

        const text = value.trim();

        return (
            text === "" ||
            text === "未显式说明"
        );

    }


    if (
        Array.isArray(value)
    ) {

        return value.length === 0;

    }


    return false;

}


function applyFunctionUpdates(
    functions,
    updates
) {

    const updatableFields =
        new Set([
            "name",
            "actor",
            "action",
            "object",
            "effect",
            "trigger",
            "condition",
            "inputs",
            "outputs",
            "preconditions",
            "postconditions",
            "scenario",
            "constraint"
        ]);


    const updateMap =
        new Map();


    (
        Array.isArray(updates)
            ? updates
            : []
    ).forEach(
        function(update) {

            if (
                update &&
                typeof update === "object" &&
                update.id
            ) {

                updateMap.set(
                    update.id,
                    update
                );

            }

        }
    );


    return (
        Array.isArray(functions)
            ? functions
            : []
    ).map(
        function(item, index) {

            const normalized =
                normalizeFunction(
                    item,
                    index
                );


            const update =
                updateMap.get(
                    normalized.id
                );


            if (!update) {

                return normalized;

            }


            const fields =
                update.fields &&
                typeof update.fields === "object"
                    ? update.fields
                    : {};


            Object.entries(fields).forEach(
                function([field, value]) {

                    if (
                        !updatableFields.has(field) ||
                        !isMissingFunctionValue(
                            normalized[field]
                        ) ||
                        isMissingFunctionValue(value)
                    ) {

                        return;

                    }


                    normalized[field] =
                        Array.isArray(value)
                            ? [...value]
                            : value;

                }
            );


            normalized.fieldCompletionEvidence = [
                ...normalized.fieldCompletionEvidence,
                {
                    fields:
                        Object.keys(fields),

                    requirementEvidence:
                        update.requirementEvidence || "",

                    historyEvidence:
                        Array.isArray(update.historyEvidence)
                            ? update.historyEvidence
                            : [],

                    evidenceType:
                        update.evidenceType || "",

                    reason:
                        update.reason || "",

                    confidence:
                        Number(update.confidence || 0)
                }
            ];


            return normalized;

        }
    );

}


// ============================================================
// 最终确认
// ============================================================

async function confirmResult() {

    if (!appState.completionReady) {

        alert(
            "请先完成AI辅助分析，再进行最终确认。"
        );

        return;

    }

    const allDecided =
        [
            ...appState.functionDecisions,
            ...appState.relationDecisions
        ].every(
            item =>
                item.status !== "pending"
        );


    if (!allDecided) {

        alert(
            "仍有AI建议未处理，请逐项选择接受、修改或拒绝。"
        );

        return;

    }


    // --------------------------------------------------------
    // 1. 获取人工接受的功能
    // --------------------------------------------------------

    const acceptedFunctions =
        appState.functionDecisions
            .filter(
                item =>
                    item.status === "accepted"
            )
            .map(
                item =>
                    normalizeFunction(
                        item.function
                    )
            );


    // --------------------------------------------------------
    // 2. 获取人工接受的关系
    // --------------------------------------------------------

    const acceptedRelations =
        appState.relationDecisions
            .filter(
                item =>
                    item.status === "accepted"
            )
            .map(
                item =>
                    normalizeRelation(
                        item.relation
                    )
            );


    // --------------------------------------------------------
    // 3. 标准化
    // --------------------------------------------------------

    // 最终模型始终只根据明确接受的建议构建。
    // 不直接采用包含全部AI候选的completionResult，防止隐藏或未决候选被误发布。
    const finalResult =
        standardizeFinalResult(
            appState.currentFunctions,
            appState.currentRelations,
            acceptedFunctions,
            acceptedRelations
        );


    appState.finalResult =
        finalResult;


    // --------------------------------------------------------
    // 4. 将人工确认后的最终模型提交给后端并发布
    // --------------------------------------------------------

    const confirmButton =
        document.getElementById(
            "finalConfirmButton"
        );


    if (confirmButton) {

        confirmButton.disabled = true;

        confirmButton.innerText =
            "正在发布确认结果...";

    }


    setSystemStatus(
        "正在发布人工确认后的最终模型",
        "running"
    );


    let publishSucceeded = false;


    try {

        const response =
            await fetch(
                "/api/completion/confirm",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify(
                        finalResult
                    )
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            const detail =
                typeof data.detail === "string"
                    ? data.detail
                    : data.message;

            throw new Error(
                detail ||
                `服务器返回HTTP ${response.status}`
            );

        }


        const publishedResult =
            data.completion_result &&
            typeof data.completion_result === "object"
                ? data.completion_result
                : finalResult;


        appState.finalResult =
            publishedResult;

        appState.completionReady = false;

        publishSucceeded = true;


        setStep(
            "step-confirm",
            "completed"
        );


        setStep(
            "step-result",
            "completed"
        );


        renderFinalModel(
            publishedResult
        );


        setSystemStatus(
            "人工确认完成，最终模型已发布",
            "confirmed"
        );


        const status =
            document.getElementById(
                "confirmationStatus"
            );


        if (status) {

            status.className =
                "status-tag confirmed";

            status.innerText =
                "已确认并发布";

        }


        alert(
            "人工确认完成，最终功能模型已成功发布。"
        );

    }

    catch (error) {

        console.error(
            "确认结果发布失败：",
            error
        );


        renderFinalModel(
            finalResult
        );


        setSystemStatus(
            "人工确认结果已生成，但发布失败",
            "error"
        );


        alert(
            "人工确认结果已生成，但发布失败：" +
            error.message +
            "。修复发布服务后可再次点击确认重试。"
        );

    }

    finally {

        if (confirmButton) {

            confirmButton.disabled =
                publishSucceeded;

            confirmButton.innerText =
                publishSucceeded
                    ? "✓ 已确认并发布"
                    : "✓ 重新确认并发布";

        }

    }

}


// ============================================================
// 标准化最终结果
// ============================================================

function standardizeFinalResult(
    currentFunctions,
    currentRelations,
    acceptedFunctions,
    acceptedRelations
) {

    const functionMap =
        new Map();


    // --------------------------------------------------------
    // 当前功能优先
    // --------------------------------------------------------

    currentFunctions.forEach(
        function(item, index) {

            const normalized =
                normalizeFunction(
                    item,
                    index
                );


            if (
                normalized.id
            ) {

                functionMap.set(
                    normalized.id,
                    normalized
                );

            }

        }
    );


    // --------------------------------------------------------
    // 人工确认后的AI功能
    // --------------------------------------------------------

    acceptedFunctions.forEach(
        function(item, index) {

            const normalized =
                normalizeFunction(
                    item,
                    currentFunctions.length + index
                );


            if (
                normalized.id
            ) {

                functionMap.set(
                    normalized.id,
                    normalized
                );

            }

        }
    );


    const functions =
        Array.from(
            functionMap.values()
        );


    // --------------------------------------------------------
    // 关系标准化
    // --------------------------------------------------------

    const relationList = [];


    [
        ...currentRelations,
        ...acceptedRelations
    ].forEach(
        function(item) {

            const relation =
                normalizeRelation(
                    item
                );


            if (
                !relation.source ||
                !relation.target
            ) {

                return;

            }


            if (
                !functionMap.has(
                    relation.source
                )
            ) {

                return;

            }


            if (
                !functionMap.has(
                    relation.target
                )
            ) {

                return;

            }


            relationList.push(
                relation
            );

        }
    );


    // --------------------------------------------------------
    // 删除重复关系
    // --------------------------------------------------------

    const relationMap =
        new Map();


    relationList.forEach(
        function(relation) {

            const key =
                [
                    relation.source,
                    relation.target,
                    relation.relation_type,
                    relation.direction,
                    relation.flowObject
                ].join(
                    "|"
                );


            if (
                !relationMap.has(key)
            ) {

                relationMap.set(
                    key,
                    relation
                );

            }

        }
    );


    return {

        functions:
            functions,

        relations:
            Array.from(
                relationMap.values()
            )

    };

}


// ============================================================
// 最终功能模型
// ============================================================

function renderFinalModel(
    result
) {

    const section =
        document.getElementById(
            "graphSection"
        );


    const container =
        document.getElementById(
            "graphResults"
        );


    if (
        !section ||
        !container
    ) {

        return;

    }


    section.classList.remove(
        "hidden"
    );


    container.innerHTML = "";


    const functions =
        Array.isArray(
            result.functions
        )
            ? result.functions
            : [];


    const relations =
        Array.isArray(
            result.relations
        )
            ? result.relations
            : [];


    if (
        functions.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                暂无最终功能语义模型
            </div>
        `;

        return;

    }


    injectGraphStyle();


    const graphInfo =
        document.createElement(
            "div"
        );


    graphInfo.className =
        "final-model-summary";


    graphInfo.innerHTML = `

        <div>
            <strong>
                ${functions.length}
            </strong>
            个功能节点
        </div>

        <div>
            <strong>
                ${relations.length}
            </strong>
            条有向关系
        </div>

        <div>
            人工确认后标准化
        </div>

    `;


    container.appendChild(
        graphInfo
    );


    const canvas =
        document.createElement(
            "div"
        );


    canvas.className =
        "semantic-graph-canvas";


    const svg =
        document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg"
        );


    svg.classList.add(
        "semantic-graph-svg"
    );


    svg.innerHTML = `

        <defs>

            <marker
                id="arrow-data"
                markerWidth="12"
                markerHeight="12"
                refX="10"
                refY="4"
                orient="auto"
                markerUnits="userSpaceOnUse"
            >

                <path
                    d="M0,0 L10,4 L0,8 z"
                    fill="#2563eb"
                />

            </marker>


            <marker
                id="arrow-control"
                markerWidth="12"
                markerHeight="12"
                refX="10"
                refY="4"
                orient="auto"
                markerUnits="userSpaceOnUse"
            >

                <path
                    d="M0,0 L10,4 L0,8 z"
                    fill="#f59e0b"
                />

            </marker>


            <marker
                id="arrow-dependency"
                markerWidth="12"
                markerHeight="12"
                refX="10"
                refY="4"
                orient="auto"
                markerUnits="userSpaceOnUse"
            >

                <path
                    d="M0,0 L10,4 L0,8 z"
                    fill="#64748b"
                />

            </marker>

        </defs>

    `;


    canvas.appendChild(
        svg
    );


    const nodeLayer =
        document.createElement(
            "div"
        );


    nodeLayer.className =
        "semantic-graph-node-layer";


    canvas.appendChild(
        nodeLayer
    );


    const positions =
        calculateGraphLayout(
            functions,
            relations
        );


    functions.forEach(
        function(item) {

            const node =
                document.createElement(
                    "div"
                );


            node.className =
                "semantic-function-node";


            node.dataset.id =
                item.id || "";


            const position =
                positions[
                    item.id
                ];


            node.style.left =
                position.x + "px";


            node.style.top =
                position.y + "px";


            node.innerHTML = `

                <div class="semantic-node-header">

                    <span class="semantic-node-id">

                        ${escapeHtml(
                            item.id || ""
                        )}

                    </span>


                    <span class="semantic-node-title">

                        ${escapeHtml(
                            item.name || ""
                        )}

                    </span>

                </div>


                <div class="semantic-node-body">

                    <div class="semantic-slot">

                        <span>
                            Actor
                        </span>

                        <strong>
                            ${escapeHtml(
                                item.actor || ""
                            )}
                        </strong>

                    </div>

                    <div class="semantic-slot">

                        <span>
                            Action
                        </span>

                        <strong>
                            ${escapeHtml(
                                item.action || ""
                            )}
                        </strong>

                    </div>


                    <div class="semantic-slot">

                        <span>
                            Object
                        </span>

                        <strong>
                            ${escapeHtml(
                                item.object || ""
                            )}
                        </strong>

                    </div>


                    <div class="semantic-slot">

                        <span>
                            Effect
                        </span>

                        <strong>
                            ${escapeHtml(
                                item.effect || ""
                            )}
                        </strong>

                    </div>


                    <div class="semantic-slot">

                        <span>
                            Input
                        </span>

                        <strong>
                            ${escapeHtml(
                                formatArray(
                                    item.inputs
                                )
                            )}
                        </strong>

                    </div>


                    <div class="semantic-slot">

                        <span>
                            Output
                        </span>

                        <strong>
                            ${escapeHtml(
                                formatArray(
                                    item.outputs
                                )
                            )}
                        </strong>

                    </div>

                </div>

            `;


            nodeLayer.appendChild(
                node
            );

        }
    );


    container.appendChild(
        canvas
    );


    requestAnimationFrame(
        function() {

            drawGraphEdges(
                svg,
                canvas,
                functions,
                relations,
                positions
            );

        }
    );


    renderGraphLegend(
        container
    );

}


// ============================================================
// 计算语义图布局
// ============================================================

function calculateGraphLayout(
    functions,
    relations
) {

    const positions = {};


    const nodeWidth =
        260;


    const nodeHeight =
        220;


    const horizontalGap =
        180;


    const verticalGap =
        90;


    const indegree = {};


    functions.forEach(
        function(item) {

            indegree[
                item.id
            ] = 0;

        }
    );


    relations.forEach(
        function(edge) {

            if (
                indegree[
                    edge.target
                ] !== undefined
            ) {

                indegree[
                    edge.target
                ]++;

            }

        }
    );


    const levels = [];


    let current =
        functions
            .filter(
                item =>
                    indegree[
                        item.id
                    ] === 0
            )
            .map(
                item =>
                    item.id
            );


    const visited =
        new Set();


    let levelIndex =
        0;


    while (
        current.length > 0
    ) {

        levels[
            levelIndex
        ] = [
            ...new Set(current)
        ];


        current.forEach(
            id =>
                visited.add(id)
        );


        const next = [];


        relations.forEach(
            function(edge) {

                if (
                    current.includes(
                        edge.source
                    )
                ) {

                    if (
                        !visited.has(
                            edge.target
                        )
                    ) {

                        next.push(
                            edge.target
                        );

                    }

                }

            }
        );


        current =
            [
                ...new Set(next)
            ];


        levelIndex++;

    }


    functions.forEach(
        function(item) {

            if (
                !visited.has(
                    item.id
                )
            ) {

                if (
                    !levels[
                        levelIndex
                    ]
                ) {

                    levels[
                        levelIndex
                    ] = [];

                }


                levels[
                    levelIndex
                ].push(
                    item.id
                );

            }

        }
    );


    levels.forEach(
        function(level, xIndex) {

            const totalHeight =
                level.length *
                nodeHeight +
                (
                    level.length - 1
                ) *
                verticalGap;


            const startY =
                Math.max(
                    70,
                    (
                        850 -
                        totalHeight
                    ) / 2
                );


            level.forEach(
                function(id, yIndex) {

                    positions[id] = {

                        x:
                            80 +
                            xIndex *
                            (
                                nodeWidth +
                                horizontalGap
                            ),

                        y:
                            startY +
                            yIndex *
                            (
                                nodeHeight +
                                verticalGap
                            )

                    };

                }
            );

        }
    );


    return positions;

}


// ============================================================
// 计算矩形节点边界交点
//
// 这是解决“箭头被节点遮挡”的关键。
// 不再让边直接从节点中心连接到节点中心。
// ============================================================

function getBoundaryPoint(
    rect,
    point
) {

    const dx =
        point.x -
        rect.cx;


    const dy =
        point.y -
        rect.cy;


    if (
        dx === 0 &&
        dy === 0
    ) {

        return {

            x: rect.cx,
            y: rect.cy

        };

    }


    const scaleX =
        rect.width / 2 /
        Math.abs(dx);


    const scaleY =
        rect.height / 2 /
        Math.abs(dy);


    const scale =
        Math.min(
            scaleX,
            scaleY
        );


    return {

        x:
            rect.cx +
            dx * scale,

        y:
            rect.cy +
            dy * scale

    };

}


// ============================================================
// 绘制关系线
// ============================================================

function drawGraphEdges(
    svg,
    canvas,
    functions,
    relations,
    positions
) {

    const nodeWidth =
        260;


    const nodeHeight =
        190;


    let maxX =
        1200;


    let maxY =
        850;


    Object.values(
        positions
    ).forEach(
        function(position) {

            maxX =
                Math.max(
                    maxX,
                    position.x +
                    nodeWidth +
                    200
                );


            maxY =
                Math.max(
                    maxY,
                    position.y +
                    nodeHeight +
                    150
                );

        }
    );


    canvas.style.width =
        maxX + "px";


    canvas.style.height =
        maxY + "px";


    svg.setAttribute(
        "viewBox",
        `0 0 ${maxX} ${maxY}`
    );


    svg.setAttribute(
        "width",
        maxX
    );


    svg.setAttribute(
        "height",
        maxY
    );


    // --------------------------------------------------------
    // 清除旧边
    // --------------------------------------------------------

    svg.querySelectorAll(
        ".graph-edge"
    ).forEach(
        element =>
            element.remove()
    );


    relations.forEach(
        function(edge, index) {

            const source =
                positions[
                    edge.source
                ];


            const target =
                positions[
                    edge.target
                ];


            if (
                !source ||
                !target
            ) {

                return;

            }


            const sourceRect = {

                cx:
                    source.x +
                    nodeWidth / 2,

                cy:
                    source.y +
                    nodeHeight / 2,

                width:
                    nodeWidth,

                height:
                    nodeHeight

            };


            const targetRect = {

                cx:
                    target.x +
                    nodeWidth / 2,

                cy:
                    target.y +
                    nodeHeight / 2,

                width:
                    nodeWidth,

                height:
                    nodeHeight

            };


            const sourceCenter = {

                x:
                    targetRect.cx,

                y:
                    targetRect.cy

            };


            const targetCenter = {

                x:
                    sourceRect.cx,

                y:
                    sourceRect.cy

            };


            // ------------------------------------------------
            // 从节点边界出发
            // ------------------------------------------------

            const start =
                getBoundaryPoint(
                    sourceRect,
                    sourceCenter
                );


            const end =
                getBoundaryPoint(
                    targetRect,
                    targetCenter
                );


            // ------------------------------------------------
            // 给箭头留出安全距离
            // ------------------------------------------------

            const dx =
                end.x -
                start.x;


            const dy =
                end.y -
                start.y;


            const distance =
                Math.sqrt(
                    dx * dx +
                    dy * dy
                );


            const safeDistance =
                Math.min(
                    14,
                    distance / 4
                );


            const ratio =
                distance > 0
                    ? safeDistance / distance
                    : 0;


            const arrowEnd = {

                x:
                    end.x -
                    dx * ratio,

                y:
                    end.y -
                    dy * ratio

            };


            // ------------------------------------------------
            // 控制点
            // ------------------------------------------------

            const middleX =
                (
                    start.x +
                    arrowEnd.x
                ) / 2;


            const middleY =
                (
                    start.y +
                    arrowEnd.y
                ) / 2;


            const path =
                document.createElementNS(
                    "http://www.w3.org/2000/svg",
                    "path"
                );


            path.classList.add(
                "graph-edge"
            );


            const pathData = `

                M ${start.x}
                  ${start.y}

                C ${middleX}
                  ${start.y},

                  ${middleX}
                  ${arrowEnd.y},

                  ${arrowEnd.x}
                  ${arrowEnd.y}

            `;


            path.setAttribute(
                "d",
                pathData
            );


            path.setAttribute(
                "fill",
                "none"
            );


            path.setAttribute(
                "stroke-linecap",
                "round"
            );


            path.setAttribute(
                "stroke-linejoin",
                "round"
            );


            const type =
                edge.relation_type ||
                "data_flow";


            if (
                type === "control_flow"
            ) {

                path.setAttribute(
                    "stroke",
                    "#f59e0b"
                );


                path.setAttribute(
                    "stroke-width",
                    "3"
                );


                path.setAttribute(
                    "marker-end",
                    "url(#arrow-control)"
                );

            }

            else if (
                type === "dependency"
            ) {

                path.setAttribute(
                    "stroke",
                    "#64748b"
                );


                path.setAttribute(
                    "stroke-width",
                    "2"
                );


                path.setAttribute(
                    "stroke-dasharray",
                    "8 6"
                );


                path.setAttribute(
                    "marker-end",
                    "url(#arrow-dependency)"
                );

            }

            else {

                path.setAttribute(
                    "stroke",
                    "#2563eb"
                );


                path.setAttribute(
                    "stroke-width",
                    "3"
                );


                path.setAttribute(
                    "marker-end",
                    "url(#arrow-data)"
                );

            }


            svg.appendChild(
                path
            );


            // ------------------------------------------------
            // 关系标签
            // ------------------------------------------------

            const labelX =
                middleX;


            const labelY =
                middleY -
                8;


            const labelText =
                type === "control_flow"
                    ? "控制流"
                    : type === "data_flow"
                        ? "数据流"
                        : type === "dependency"
                            ? "依赖关系"
                            : type;


            if (
                !labelText
            ) {

                return;

            }


            const labelWidth =
                Math.max(
                    90,
                    Math.min(
                        180,
                        labelText.length * 14 + 20
                    )
                );


            const labelBackground =
                document.createElementNS(
                    "http://www.w3.org/2000/svg",
                    "rect"
                );


            labelBackground.classList.add(
                "graph-edge"
            );


            labelBackground.setAttribute(
                "x",
                labelX -
                labelWidth / 2
            );


            labelBackground.setAttribute(
                "y",
                labelY -
                16
            );


            labelBackground.setAttribute(
                "width",
                labelWidth
            );


            labelBackground.setAttribute(
                "height",
                26
            );


            labelBackground.setAttribute(
                "rx",
                6
            );


            labelBackground.setAttribute(
                "fill",
                "#ffffff"
            );


            labelBackground.setAttribute(
                "stroke",
                "#cbd5e1"
            );


            svg.appendChild(
                labelBackground
            );


            const label =
                document.createElementNS(
                    "http://www.w3.org/2000/svg",
                    "text"
                );


            label.classList.add(
                "graph-edge"
            );


            label.setAttribute(
                "x",
                labelX
            );


            label.setAttribute(
                "y",
                labelY + 1
            );


            label.setAttribute(
                "text-anchor",
                "middle"
            );


            label.setAttribute(
                "dominant-baseline",
                "middle"
            );


            label.setAttribute(
                "font-size",
                "12"
            );


            label.setAttribute(
                "font-weight",
                "600"
            );


            label.setAttribute(
                "fill",
                "#334155"
            );


            label.textContent =
                labelText;


            svg.appendChild(
                label
            );

        }
    );

}


// ============================================================
// 图例
// ============================================================

function renderGraphLegend(
    container
) {

    const legend =
        document.createElement(
            "div"
        );


    legend.className =
        "semantic-graph-legend";


    legend.innerHTML = `

        <div class="legend-title">
            功能关系图例
        </div>


        <div class="legend-item">

            <span class="legend-line data">
            </span>

            数据流 →

        </div>


        <div class="legend-item">

            <span class="legend-line control">
            </span>

            控制流 →

        </div>


        <div class="legend-item">

            <span class="legend-line dependency">
            </span>

            依赖关系 →

        </div>

    `;


    container.appendChild(
        legend
    );

}


// ============================================================
// 图样式
// ============================================================

function injectGraphStyle() {

    if (
        document.getElementById(
            "semanticGraphStyle"
        )
    ) {

        return;

    }


    const style =
        document.createElement(
            "style"
        );


    style.id =
        "semanticGraphStyle";


    style.innerHTML = `

        .semantic-graph-canvas {

            position: relative;

            min-width: 1200px;

            min-height: 850px;

            overflow: auto;

            background:
                linear-gradient(
                    #f1f5f9 1px,
                    transparent 1px
                ),
                linear-gradient(
                    90deg,
                    #f1f5f9 1px,
                    transparent 1px
                );

            background-size:
                20px 20px;

            border:
                1px solid #dbe3ea;

            border-radius:
                10px;

            margin-top:
                20px;

        }


        .semantic-graph-svg {

            position:
                absolute;

            left:
                0;

            top:
                0;

            z-index:
                3;

            pointer-events:
                none;

            overflow:
                visible;

        }


        .semantic-graph-node-layer {

            position:
                absolute;

            left:
                0;

            top:
                0;

            width:
                100%;

            height:
                100%;

            z-index:
                2;

            pointer-events:
                none;

        }


        .semantic-function-node {

            position:
                absolute;

            width:
                260px;

            min-height:
                190px;

            box-sizing:
                border-box;

            background:
                #ffffff;

            border:
                2px solid #64748b;

            border-radius:
                10px;

            box-shadow:
                0 4px 14px
                rgba(
                    15,
                    23,
                    42,
                    0.12
                );

            overflow:
                hidden;

        }


        .semantic-node-header {

            display:
                flex;

            align-items:
                center;

            gap:
                8px;

            padding:
                10px 12px;

            background:
                #e8f1f8;

            border-bottom:
                1px solid #cbd5e1;

        }


        .semantic-node-id {

            display:
                inline-block;

            padding:
                3px 7px;

            border-radius:
                4px;

            background:
                #334155;

            color:
                #ffffff;

            font-size:
                12px;

            font-weight:
                600;

        }


        .semantic-node-title {

            font-size:
                14px;

            font-weight:
                700;

            color:
                #1e293b;

            line-height:
                1.4;

        }


        .semantic-node-body {

            padding:
                11px 12px;

        }


        .semantic-slot {

            display:
                flex;

            align-items:
                flex-start;

            gap:
                8px;

            margin-bottom:
                7px;

            font-size:
                12px;

            line-height:
                1.45;

        }


        .semantic-slot span {

            flex:
                0 0 52px;

            color:
                #64748b;

            font-weight:
                600;

        }


        .semantic-slot strong {

            flex:
                1;

            color:
                #334155;

            font-weight:
                500;

            word-break:
                break-all;

        }


        .semantic-graph-legend {

            display:
                flex;

            align-items:
                center;

            flex-wrap:
                wrap;

            gap:
                20px;

            margin:
                12px 0 20px;

            padding:
                10px 14px;

            border:
                1px solid #e2e8f0;

            border-radius:
                8px;

            background:
                #ffffff;

            font-size:
                13px;

        }


        .legend-title {

            font-weight:
                700;

            color:
                #334155;

        }


        .legend-item {

            display:
                flex;

            align-items:
                center;

            gap:
                6px;

            color:
                #475569;

        }


        .legend-line {

            display:
                inline-block;

            width:
                30px;

            height:
                3px;

        }


        .legend-line.data {

            background:
                #2563eb;

        }


        .legend-line.control {

            background:
                #f59e0b;

        }


        .legend-line.dependency {

            height:
                0;

            border-top:
                3px dashed #64748b;

        }

    `;


    document.head.appendChild(
        style
    );

}


// ============================================================
// 统计信息
// ============================================================

function updateStatistics(
    data
) {

    const functions =
        appState.functionDecisions;


    const relations =
        appState.relationDecisions;


    const functionCount =
        document.getElementById(
            "functionCount"
        );


    if (functionCount) {

        functionCount.innerText =
            functions.length;

    }


    const relationCount =
        document.getElementById(
            "relationCount"
        );


    if (relationCount) {

        relationCount.innerText =
            relations.length;

    }


    updateConfirmationProgress();

}


// ============================================================
// 决策文字
// ============================================================

function getDecisionText(
    status
) {

    if (
        status === "accepted"
    ) {

        return "已接受";

    }


    if (
        status === "rejected"
    ) {

        return "已拒绝";

    }


    return "待确认";

}


// ============================================================
// DOM工具
// ============================================================

function hideElement(
    id
) {

    const element =
        document.getElementById(
            id
        );


    if (element) {

        element.classList.add(
            "hidden"
        );

    }

}
