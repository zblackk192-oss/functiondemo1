import json


def _normalize_list(value):

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _compact_function(function):
    """
    Prompt中的标准功能结构。
    """

    if not isinstance(
        function,
        dict
    ):
        return {}

    return {
        "functionId": function.get(
            "functionId",
            ""
        ),

        "name": function.get(
            "name",
            ""
        ),

        "action": function.get(
            "action",
            ""
        ),

        "object": function.get(
            "object",
            ""
        ),

        "effect": function.get(
            "effect",
            ""
        ),

        "trigger": function.get(
            "trigger",
            ""
        ),

        "condition": function.get(
            "condition",
            ""
        ),

        "inputs": _normalize_list(
            function.get(
                "inputs",
                function.get(
                    "input",
                    []
                )
            )
        ),

        "outputs": _normalize_list(
            function.get(
                "outputs",
                function.get(
                    "output",
                    []
                )
            )
        ),

        "preconditions": _normalize_list(
            function.get(
                "preconditions",
                []
            )
        ),

        "postconditions": _normalize_list(
            function.get(
                "postconditions",
                []
            )
        ),

        "scenario": function.get(
            "scenario",
            ""
        ),

        "constraint": function.get(
            "constraint",
            ""
        ),

        "rawstatements": function.get(
            "rawstatements",
            ""
        )
    }


def _compact_relation(relation):
    """
    Prompt中的标准关系结构。
    """

    if not isinstance(
        relation,
        dict
    ):
        return {}

    return {
        "source": relation.get(
            "source",
            ""
        ),

        "target": relation.get(
            "target",
            ""
        ),

        "type": relation.get(
            "type",
            ""
        ),

        "flowObject": relation.get(
            "flowObject",
            ""
        )
    }


def _compact_retrieved_case(item):
    """
    将RAG命中结果转换成历史局部功能模式。

    不再只给Qwen一个孤立功能。

    同时提供：

        matchedFunction
        neighborFunctions
        relatedRelations
    """

    if not isinstance(
        item,
        dict
    ):
        return {}

    data = item.get(
        "data",
        {}
    )

    if not isinstance(
        data,
        dict
    ):
        data = {}

    matched_function = data.get(
        "function",
        {}
    )

    neighbor_functions = data.get(
        "neighborFunctions",
        []
    )

    related_relations = data.get(
        "relatedRelations",
        []
    )

    if not isinstance(
        neighbor_functions,
        list
    ):
        neighbor_functions = []

    if not isinstance(
        related_relations,
        list
    ):
        related_relations = []

    return {
        "caseId": data.get(
            "caseId",
            ""
        ),

        "similarity": item.get(
            "score",
            0
        ),

        "matchedFunction":
            _compact_function(
                matched_function
            ),

        "neighborFunctions": [
            _compact_function(
                function
            )
            for function
            in neighbor_functions
            if isinstance(
                function,
                dict
            )
        ],

        "relatedRelations": [
            _compact_relation(
                relation
            )
            for relation
            in related_relations
            if isinstance(
                relation,
                dict
            )
        ]
    }


def build_completion_prompt(
    raw_text,
    current_functions,
    current_relations,
    history_functions,
    function_points=None,
    events=None
):
    """
    构造证据驱动的RAG功能补全Prompt。

    核心思想：

        当前需求
        +
        当前已有模型
        +
        Top-K历史局部功能子图
        ↓
        Qwen分析历史模式
        ↓
        迁移到当前案例
        ↓
        缺失功能/关系候选
    """

    if function_points is None:
        function_points = []

    if events is None:
        events = []

    # ------------------------------------------------------
    # 当前功能
    # ------------------------------------------------------

    current_function_data = [
        _compact_function(
            function
        )
        for function
        in current_functions
        if isinstance(
            function,
            dict
        )
    ]

    # ------------------------------------------------------
    # 当前关系
    # ------------------------------------------------------

    current_relation_data = [
        _compact_relation(
            relation
        )
        for relation
        in current_relations
        if isinstance(
            relation,
            dict
        )
    ]

    # ------------------------------------------------------
    # 历史局部模式
    # ------------------------------------------------------

    history_data = [
        _compact_retrieved_case(
            item
        )
        for item
        in history_functions
        if isinstance(
            item,
            dict
        )
    ]

    prompt = f"""
你是一名汽车系统功能架构设计专家。

你的任务不是简单复述当前需求，也不是简单复制历史案例。

你的任务是：

利用当前需求、当前已有功能模型以及RAG检索得到的历史汽车系统功能模式，
识别当前设计中可能缺失的功能点和缺失的关联关系。


============================================================
一、必须遵循的推理原则
============================================================

1. 当前functions和relations表示“已经建模的内容”，不代表设计一定完整。

2. raw_text、function_points和events表示当前案例的需求语义，
可用于识别当前设计中明确遗漏的内容。

3. RAG历史案例不是普通背景资料，而是补全的重要证据。

4. 对每一个RAG命中案例，重点分析：

   matchedFunction：
       与当前功能语义相似的历史功能。

   neighborFunctions：
       该历史功能直接连接的上游或下游功能。

   relatedRelations：
       历史案例中该功能与邻居功能之间的关系。

5. 必须主动寻找历史案例中反复出现的局部功能模式，例如：

       A -> B
       A -> C

   如果当前设计只有A和B，
   而多个高相似历史案例都存在A->C模式，
   应判断C是否可能是当前设计缺失功能。

6. 对关系补全也采用同样原则。

   如果历史案例中存在：

       A -> B data_flow

   当前案例存在语义对应的A和B，
   但当前relations中没有对应关系，
   应将其作为missingRelations候选。

7. 历史案例中的functionId只属于历史案例。

   不允许直接把历史functionId复制到当前案例。

   必须根据语义找到当前案例中的对应功能。

8. 如果历史邻居功能在当前案例中不存在，
   但该功能模式与当前需求、对象、场景一致，
   可以生成新的missingFunction。

9. 如果新增missingFunction参与missingRelation，
   missingRelation必须引用该新增功能的functionId。

10. 不允许输出当前已经存在的功能。

11. 不允许输出当前已经存在的关系。

12. 历史案例只是证据。
    如果历史功能明显不适用于当前系统对象、场景或约束，
    不得强行迁移。

13. 不要因为raw_text可以直接恢复某个功能，
    就忽略历史案例。

    必须同时检查历史案例是否还能提供：
        - 当前需求没有显式写出的合理功能；
        - 当前设计缺失的上下游功能；
        - 当前设计缺失的数据流；
        - 当前设计缺失的控制流；
        - 当前功能之间缺失的关联模式。

14. 如果当前需求直接支持某候选，
    同时历史案例也支持，
    evidenceType使用：

        requirement_and_history

15. 如果主要由当前需求直接推导，
    历史案例没有明显支持，
    evidenceType使用：

        requirement_only

16. 如果当前需求没有直接写出，
    但多个高相似历史案例提供一致模式，
    且该模式适用于当前场景，
    evidenceType使用：

        history_only

17. confidence范围必须为0到1。

18. 输出必须是合法JSON。

19. 不要输出Markdown代码块。

20. 不要输出JSON之外的任何解释文字。


============================================================
二、当前原始需求
============================================================

{raw_text}


============================================================
三、当前需求功能点
============================================================

{json.dumps(
    function_points,
    ensure_ascii=False,
    indent=2
)}


============================================================
四、当前需求事件
============================================================

{json.dumps(
    events,
    ensure_ascii=False,
    indent=2
)}


============================================================
五、当前已经存在的功能
============================================================

{json.dumps(
    current_function_data,
    ensure_ascii=False,
    indent=2
)}


============================================================
六、当前已经存在的关系
============================================================

{json.dumps(
    current_relation_data,
    ensure_ascii=False,
    indent=2
)}


============================================================
七、RAG Top-K历史局部功能模式
============================================================

{json.dumps(
    history_data,
    ensure_ascii=False,
    indent=2
)}


============================================================
八、分析要求
============================================================

请综合执行以下分析：

A. 当前需求缺口分析

检查raw_text、function_points、events中是否存在当前functions尚未建模的功能。


B. 历史功能模式分析

逐个分析RAG案例中的：

matchedFunction
neighborFunctions
relatedRelations

判断历史案例中是否存在当前设计尚未包含的功能模式。


C. 历史关系模式分析

重点比较：

历史：
matchedFunction -> neighborFunction

当前：
对应功能 -> 对应功能

如果当前两个功能都存在，但关系不存在，
生成missingRelation候选。


D. 历史邻居迁移

如果历史neighborFunction在当前设计中没有对应功能，
但：

- 相似度较高；
- 与当前对象一致；
- 与当前场景一致；
- 与当前需求不冲突；

则可以生成missingFunction候选。


E. 证据说明

每个missingFunction必须说明：

requirementEvidence
historyEvidence
evidenceType
reason
confidence

每个missingRelation也必须说明：

historyEvidence
evidenceType
reason
confidence


============================================================
九、输出格式
============================================================

{{
  "missingFunctions": [
    {{
      "functionId": "FXXX",
      "name": "",
      "action": "",
      "object": "",
      "effect": "",
      "trigger": "",
      "condition": "",
      "inputs": [],
      "outputs": [],
      "preconditions": [],
      "postconditions": [],
      "scenario": "",
      "constraint": "",

      "requirementEvidence": "",
      "historyEvidence": [
        {{
          "caseId": "",
          "matchedFunctionId": "",
          "neighborFunctionId": "",
          "similarity": 0.0,
          "matchedPattern": ""
        }}
      ],

      "evidenceType": "requirement_and_history",
      "reason": "",
      "confidence": 0.0
    }}
  ],

  "missingRelations": [
    {{
      "source": "FXXX",
      "target": "FXXX",
      "type": "data_flow",
      "flowObject": "",

      "historyEvidence": [
        {{
          "caseId": "",
          "source": "",
          "target": "",
          "type": "",
          "similarity": 0.0
        }}
      ],

      "evidenceType": "history_only",
      "reason": "",
      "confidence": 0.0
    }}
  ]
}}
"""

    return prompt