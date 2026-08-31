"""
三元组审核组件
"""

import streamlit as st
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import copy
from html import escape as html_escape

from components.icons import icon


@dataclass
class TripleReviewState:
    """三元组审核状态"""
    triples: List[Dict] = field(default_factory=list)
    review_status: Dict[int, str] = field(default_factory=dict)  # {index: 'pending'|'confirmed'|'edited'|'deleted'}
    edited_triples: Dict[int, Dict] = field(default_factory=dict)
    current_page: int = 0
    page_size: int = 10

    @property
    def confirmed_count(self) -> int:
        return sum(1 for s in self.review_status.values() if s == 'confirmed')

    @property
    def edited_count(self) -> int:
        return sum(1 for s in self.review_status.values() if s == 'edited')

    @property
    def deleted_count(self) -> int:
        return sum(1 for s in self.review_status.values() if s == 'deleted')

    @property
    def pending_count(self) -> int:
        return sum(1 for s in self.review_status.values() if s == 'pending')

    @property
    def total_to_save(self) -> int:
        return self.confirmed_count + self.edited_count

    def get_triples_to_save(self) -> List[Dict]:
        """获取需要保存的三元组"""
        result = []
        for i, triple in enumerate(self.triples):
            status = self.review_status.get(i, 'pending')
            if status == 'confirmed':
                result.append(triple)
            elif status == 'edited':
                result.append(self.edited_triples.get(i, triple))
        return result


def init_review_state(triples: List[Dict]) -> TripleReviewState:
    """初始化审核状态"""
    state = TripleReviewState(
        triples=triples,
        review_status={i: 'pending' for i in range(len(triples))}
    )
    return state


def render_review_panel(review_state: TripleReviewState) -> Tuple[str, Optional[int]]:
    """
    渲染审核面板

    Args:
        review_state: 审核状态

    Returns:
        (动作, 三元组索引) 或 ('', None)

    动作契约：
        edit_start  : 用户点击"编辑"，已设置 review_editing_idx，需 rerun
        edit_save   : 用户在编辑表单点击"保存"，编辑结果存于 _pending_edited_triple
        edit_cancel : 用户取消编辑
        confirm / delete / confirm_all / skip_review / complete : 原有语义
    """
    st.markdown("### ✅ 三元组审核")

    # ---- 编辑表单（置顶，处于编辑态时优先渲染，确保跨 rerun 可保存） ----
    editing_idx = st.session_state.get('review_editing_idx')
    if editing_idx is not None and 0 <= editing_idx < len(review_state.triples):
        action, edited = render_triple_edit_modal(
            editing_idx, review_state.triples[editing_idx]
        )
        if action == 'save' and edited:
            st.session_state['_pending_edited_triple'] = edited
            return ('edit_save', editing_idx)
        elif action == 'cancel':
            return ('edit_cancel', editing_idx)
        st.markdown('<hr style="border: none; border-top: 1px solid var(--border-light); margin: 1rem 0;">', unsafe_allow_html=True)

    # 统计信息
    render_review_statistics(review_state)

    st.markdown("---")

    # 分页控制
    total_pages = max(1, (len(review_state.triples) - 1) // review_state.page_size + 1)
    if review_state.current_page >= total_pages:
        review_state.current_page = max(0, total_pages - 1)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("上一页", disabled=review_state.current_page == 0):
            review_state.current_page -= 1
            return ('prev_page', None)

    with col2:
        st.markdown(
            f'<div style="text-align: center; color: var(--text-secondary);">第 {review_state.current_page + 1}/{total_pages} 页</div>',
            unsafe_allow_html=True
        )

    with col3:
        if st.button("下一页", disabled=review_state.current_page >= total_pages - 1):
            review_state.current_page += 1
            return ('next_page', None)

    st.markdown("---")

    # 当前页的三元组
    start_idx = review_state.current_page * review_state.page_size
    end_idx = min(start_idx + review_state.page_size, len(review_state.triples))

    for idx in range(start_idx, end_idx):
        triple = review_state.triples[idx]
        edited_triple = review_state.edited_triples.get(idx)
        status = review_state.review_status.get(idx, 'pending')

        action = render_triple_card(idx, triple, edited_triple, status)

        if action == 'edit':
            # 进入编辑态：记住正在编辑的索引，下一轮渲染编辑表单
            st.session_state['review_editing_idx'] = idx
            return ('edit_start', idx)
        elif action:
            return (action, idx)

    # 快捷操作按钮
    st.markdown("---")
    return render_quick_actions(review_state)


def render_review_statistics(review_state: TripleReviewState):
    """渲染审核统计"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("已确认", review_state.confirmed_count)
    with col2:
        st.metric("已编辑", review_state.edited_count)
    with col3:
        st.metric("已删除", review_state.deleted_count)
    with col4:
        st.metric("待审核", review_state.pending_count)

    # 进度
    if len(review_state.triples) > 0:
        reviewed_count = len(review_state.triples) - review_state.pending_count
        progress = reviewed_count / len(review_state.triples)

        st.progress(progress)
        st.markdown(
            f'<div style="text-align: center; color: var(--text-muted);">审核进度: {progress*100:.1f}% ({reviewed_count}/{len(review_state.triples)})</div>',
            unsafe_allow_html=True
        )


def render_triple_card(idx: int, triple: Dict, edited_triple: Optional[Dict],
                       status: str) -> Optional[str]:
    """
    渲染单个三元组卡片

    Returns:
        动作字符串或None
    """
    # 使用编辑后的版本（如果有）
    display_triple = edited_triple or triple

    # 状态样式（SVG 图标替代 emoji，跨系统颜色/尺寸一致）
    status_styles = {
        'pending': (icon("clock", 13, "#92400E") + " 待审核", 'warning'),
        'confirmed': (icon("check", 13, "#047857") + " 已确认", 'success'),
        'edited': (icon("edit", 13, "#2563EB") + " 已编辑", 'info'),
        'deleted': (icon("x", 13, "#991B1B") + " 已删除", 'error')
    }
    status_text, status_type = status_styles.get(status, (icon("circle", 13, "#6B7280") + " 未知", 'secondary'))

    # 对三元组值进行HTML转义，防止注入
    head_name = html_escape(str(display_triple.get('head', 'N/A')))
    head_type = html_escape(str(display_triple.get('head_type', 'N/A')))
    head_props_html = html_escape(format_properties(display_triple.get('head_properties', {})))
    relation = html_escape(str(display_triple.get('relation', 'N/A')))
    tail_name = html_escape(str(display_triple.get('tail', 'N/A')))
    tail_type = html_escape(str(display_triple.get('tail_type', 'N/A')))
    tail_props_html = html_escape(format_properties(display_triple.get('tail_properties', {})))

    # 卡片HTML - 单行避免markdown解析器干扰
    card_html = (
        f'<div class="triple-card" style="--index: {idx % 10}; margin-bottom: 1rem;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
        f'<span style="color: var(--text-muted);">三元组 #{idx + 1}</span>'
        f'<span class="file-status {status_type}">{status_text}</span>'
        f'</div>'
        f'<div class="triple-content">'
        f'<div class="entity">'
        f'<div class="entity-name">{head_name}</div>'
        f'<div class="entity-type">{head_type}</div>'
        f'<div class="entity-properties">{head_props_html}</div>'
        f'</div>'
        f'<div class="relation">{relation}</div>'
        f'<div class="entity">'
        f'<div class="entity-name">{tail_name}</div>'
        f'<div class="entity-type">{tail_type}</div>'
        f'<div class="entity-properties">{tail_props_html}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    # 操作按钮
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✓ 确认", key=f"confirm_{idx}", use_container_width=True,
                     disabled=status == 'confirmed'):
            return 'confirm'

    with col2:
        if st.button("编辑", key=f"edit_{idx}", use_container_width=True):
            return 'edit'

    with col3:
        if st.button("✕ 删除", key=f"delete_{idx}", use_container_width=True,
                     disabled=status == 'deleted'):
            return 'delete'

    return None


def render_triple_edit_modal(idx: int, triple: Dict) -> Tuple[str, Optional[Dict]]:
    """
    渲染三元组编辑表单（置顶卡片，跨 rerun 保持可保存）

    Args:
        idx: 三元组索引
        triple: 原始三元组

    Returns:
        (动作, 编辑后的三元组) 动作: '' | 'save' | 'cancel'
    """
    st.markdown(
        '<div style="background: var(--color-primary-50); border: 1px solid var(--color-primary-200); '
        'border-radius: var(--radius-lg); padding: 1rem 1.25rem; margin-bottom: 0.75rem;">'
        '<div style="font-weight: 600; color: var(--color-primary-700); margin-bottom: 0.5rem;">✏ 编辑三元组 #' + str(idx + 1) + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    col_h, col_r, col_t = st.columns(3)
    with col_h:
        st.markdown("**头实体**")
        head = st.text_input("名称", value=triple.get('head', ''), key=f"edit_head_{idx}", label_visibility="collapsed")
        head_type = st.text_input("类型", value=triple.get('head_type', ''), key=f"edit_head_type_{idx}", label_visibility="collapsed")
        st.caption("头实体属性")
        head_props = render_properties_editor(triple.get('head_properties', {}), f"head_{idx}")
    with col_r:
        st.markdown("**关系**")
        relation = st.text_input("关系类型", value=triple.get('relation', ''), key=f"edit_relation_{idx}", label_visibility="collapsed")
    with col_t:
        st.markdown("**尾实体**")
        tail = st.text_input("名称", value=triple.get('tail', ''), key=f"edit_tail_{idx}", label_visibility="collapsed")
        tail_type = st.text_input("类型", value=triple.get('tail_type', ''), key=f"edit_tail_type_{idx}", label_visibility="collapsed")
        st.caption("尾实体属性")
        tail_props = render_properties_editor(triple.get('tail_properties', {}), f"tail_{idx}")

    # 按钮
    col1, col2 = st.columns(2)
    with col1:
        cancel_clicked = st.button("取消", key=f"cancel_edit_{idx}", use_container_width=True)
    with col2:
        save_clicked = st.button("保存", key=f"save_edit_{idx}", type="primary", use_container_width=True)

    if save_clicked:
        edited_triple = {
            'head': head,
            'head_type': head_type,
            'head_properties': head_props,
            'relation': relation,
            'tail': tail,
            'tail_type': tail_type,
            'tail_properties': tail_props
        }
        _clear_new_prop_slots(idx)
        return 'save', edited_triple

    if cancel_clicked:
        _clear_new_prop_slots(idx)
        return 'cancel', None

    return '', None


def _clear_new_prop_slots(idx: int):
    """清理编辑表单中动态新增属性行的 session_state，避免下次编辑残留"""
    for prefix in (f"head_{idx}", f"tail_{idx}"):
        st.session_state.pop(f"_new_props_{prefix}", None)


def render_properties_editor(properties: Dict, prefix: str) -> Dict:
    """渲染属性编辑器（支持编辑已有属性 + 动态新增多组属性）"""
    edited_props = {}

    # 已有属性
    for key, value in properties.items():
        new_value = st.text_input(
            str(key),
            value=str(value),
            key=f"prop_{prefix}_{key}",
            label_visibility="collapsed",
            placeholder=str(key)
        )
        edited_props[key] = new_value

    # 新增属性（动态多行）
    new_props_key = f"_new_props_{prefix}"
    if new_props_key not in st.session_state:
        st.session_state[new_props_key] = [{}]

    st.markdown('<div style="font-size: 0.75rem; color: var(--text-tertiary); margin: 0.25rem 0;">新增属性</div>', unsafe_allow_html=True)
    for i, slot in enumerate(st.session_state[new_props_key]):
        ck, cv = st.columns(2)
        with ck:
            slot['key'] = st.text_input("属性名", value=slot.get('key', ''), key=f"newk_{prefix}_{i}", label_visibility="collapsed", placeholder="属性名")
        with cv:
            slot['value'] = st.text_input("属性值", value=slot.get('value', ''), key=f"newv_{prefix}_{i}", label_visibility="collapsed", placeholder="属性值")
        if slot.get('key'):
            edited_props[slot['key']] = slot.get('value', '')

    if st.button("+ 添加属性行", key=f"addprop_{prefix}", use_container_width=True):
        st.session_state[new_props_key].append({})
        st.rerun()

    return edited_props


def render_quick_actions(review_state: TripleReviewState) -> Tuple[str, Optional[int]]:
    """渲染快捷操作"""

    st.markdown("#### 快捷操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("全部确认", key="confirm_all", use_container_width=True):
            return ('confirm_all', None)

    with col2:
        if st.button("跳过审核", key="skip_review", use_container_width=True,
                     help="直接使用原始抽取结果，不进行修改"):
            return ('skip_review', None)

    with col3:
        if st.button("完成审核", key="complete_review", type="primary",
                     use_container_width=True,
                     disabled=review_state.total_to_save == 0):
            return ('complete', None)

    return ('', None)


def format_properties(props: Dict) -> str:
    """格式化属性显示"""
    if not props:
        return ""

    items = []
    for k, v in props.items():
        items.append(f"{html_escape(str(k))}: {html_escape(str(v))}")

    return ", ".join(items[:3]) + ("..." if len(items) > 3 else "")


def apply_review_action(review_state: TripleReviewState, action: str, idx: int,
                        edited_triple: Dict = None):
    """
    应用审核动作

    Args:
        review_state: 审核状态
        action: 动作类型
        idx: 三元组索引
        edited_triple: 编辑后的三元组（编辑动作时）
    """
    if action == 'confirm':
        review_state.review_status[idx] = 'confirmed'

    elif action == 'delete':
        review_state.review_status[idx] = 'deleted'

    elif action == 'edit' and edited_triple:
        review_state.review_status[idx] = 'edited'
        review_state.edited_triples[idx] = edited_triple

    elif action == 'confirm_all':
        for i in review_state.review_status:
            if review_state.review_status[i] == 'pending':
                review_state.review_status[i] = 'confirmed'

    elif action == 'skip_review':
        # 所有待审核的都确认
        for i in review_state.review_status:
            review_state.review_status[i] = 'confirmed'


def save_review_state(review_state: TripleReviewState):
    """保存审核状态到session_state"""
    st.session_state['triples_review_state'] = {
        'triples': review_state.triples,
        'review_status': review_state.review_status,
        'edited_triples': review_state.edited_triples,
        'current_page': review_state.current_page
    }