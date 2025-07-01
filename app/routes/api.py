"""
API路由
"""

from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from flask_login import login_required, current_user
import uuid
from datetime import datetime, timedelta
import logging
import json
import threading
import time
from queue import Queue
import traceback

from app.models import User, KnowledgeBase, Conversation, Message
from app.database import db
from app.services import DeepSeekService
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# DeepSeek服务将在使用时初始化
deepseek_service = None

# 消息保存队列
message_save_queue = Queue()
message_save_thread = None

def get_deepseek_service():
    """获取DeepSeek服务实例"""
    global deepseek_service
    if deepseek_service is None:
        deepseek_service = DeepSeekService()
    return deepseek_service

def save_message_worker():
    """独立线程工作器，专门处理消息保存"""
    import queue
    from app import create_app
    
    # 创建独立的应用实例
    app = create_app()
    
    logger.info("🔧 消息保存工作线程已启动，等待消息...")
    
    while True:
        try:
            # 从队列获取待保存的消息数据
            save_data = message_save_queue.get(timeout=30)  # 30秒超时
            
            if save_data is None:  # 停止信号
                logger.info("🔚 收到停止信号，消息保存工作线程退出")
                break
                
            conversation_id = save_data['conversation_id']
            ai_msg_id = save_data['ai_msg_id']
            ai_response = save_data['ai_response']
            debug_info = save_data['debug_info']
            user_id = save_data['user_id']
            retry_count = save_data.get('retry_count', 0)
            
            debug_info['db_operations'] = debug_info.get('db_operations', [])
            
            try:
                # 使用独立的应用上下文
                with app.app_context():
                    # 记录数据库操作开始
                    operation_start = time.time()
                    debug_info['db_operations'].append({
                        'operation': 'save_ai_message_start',
                        'timestamp': operation_start,
                        'thread_id': threading.current_thread().ident,
                        'ai_msg_id': ai_msg_id,
                        'conversation_id': conversation_id,
                        'response_length': len(ai_response),
                        'retry_count': retry_count
                    })
                    
                    # 验证对话是否存在
                    conversation = db.session.query(Conversation).filter_by(
                        id=conversation_id,
                        user_id=user_id
                    ).first()
                    
                    if not conversation:
                        debug_info['db_operations'].append({
                            'operation': 'conversation_not_found',
                            'timestamp': time.time(),
                            'conversation_id': conversation_id,
                            'error': '对话不存在'
                        })
                        logger.error(f"保存消息失败：对话 {conversation_id} 不存在")
                        message_save_queue.task_done()
                        continue
                    
                    # 检查消息是否已存在（防止重复保存）
                    existing_msg = db.session.query(Message).filter_by(id=ai_msg_id).first()
                    if existing_msg:
                        debug_info['db_operations'].append({
                            'operation': 'message_already_exists',
                            'timestamp': time.time(),
                            'ai_msg_id': ai_msg_id,
                            'existing_content_length': len(existing_msg.content)
                        })
                        logger.info(f"消息 {ai_msg_id} 已存在，跳过保存")
                        message_save_queue.task_done()
                        continue
                    
                    # 保存AI消息
                    ai_msg = Message(
                        id=ai_msg_id,
                        conversation_id=conversation_id,
                        role='assistant',
                        content=ai_response,
                        token_count=len(ai_response.split()),  # 简单的token计算
                        created_at=datetime.utcnow()
                    )
                    db.session.add(ai_msg)
                    
                    # 更新对话信息
                    conversation.message_count += 1
                    conversation.updated_at = datetime.utcnow()
                    
                    # 提交事务
                    db.session.commit()
                    
                    operation_end = time.time()
                    debug_info['db_operations'].append({
                        'operation': 'save_ai_message_success',
                        'timestamp': operation_end,
                        'duration': operation_end - operation_start,
                        'ai_msg_id': ai_msg_id,
                        'conversation_id': conversation_id,
                        'new_message_count': conversation.message_count,
                        'commit_successful': True
                    })
                    
                    logger.info(f"✅ AI消息已成功保存: {ai_msg_id}, 对话: {conversation_id}, 耗时: {operation_end - operation_start:.3f}s")
                    
                    # 🔥 重要：通知LangChain服务刷新历史记录
                    try:
                        from app.services.conversation_service import ConversationService
                        conv_service = ConversationService()
                        if conv_service.langchain_enabled and conv_service.langchain_service:
                            # 清除该对话的历史缓存，强制重新加载
                            if conversation_id in conv_service.langchain_service._session_histories:
                                conv_service.langchain_service._session_histories[conversation_id].reload_from_database()
                                debug_info['db_operations'].append({
                                    'operation': 'langchain_history_refreshed',
                                    'timestamp': time.time(),
                                    'conversation_id': conversation_id
                                })
                                logger.info(f"🔄 LangChain历史记录已刷新: {conversation_id}")
                    except Exception as refresh_error:
                        debug_info['db_operations'].append({
                            'operation': 'langchain_refresh_error',
                            'timestamp': time.time(),
                            'error': str(refresh_error)
                        })
                        logger.warning(f"LangChain历史刷新失败: {str(refresh_error)}")
                    
            except Exception as save_error:
                error_time = time.time()
                debug_info['db_operations'].append({
                    'operation': 'save_ai_message_error',
                    'timestamp': error_time,
                    'error': str(save_error),
                    'error_type': type(save_error).__name__,
                    'traceback': traceback.format_exc(),
                    'retry_count': retry_count
                })
                
                logger.error(f"❌ 保存AI消息失败 (尝试 {retry_count + 1}): {str(save_error)}")
                
                # 回滚数据库事务
                try:
                    with app.app_context():
                        db.session.rollback()
                except Exception as rollback_error:
                    debug_info['db_operations'].append({
                        'operation': 'rollback_error',
                        'timestamp': time.time(),
                        'error': str(rollback_error)
                    })
                
                # 重试机制（最多重试3次）
                if retry_count < 3:
                    save_data['retry_count'] = retry_count + 1
                    debug_info['db_operations'].append({
                        'operation': 'retry_scheduled',
                        'timestamp': time.time(),
                        'retry_count': retry_count + 1,
                        'delay': 2 ** retry_count  # 指数退避
                    })
                    
                    # 延迟后重新加入队列
                    def retry_save():
                        time.sleep(2 ** retry_count)  # 指数退避：1s, 2s, 4s
                        message_save_queue.put(save_data)
                    
                    threading.Thread(target=retry_save, daemon=True).start()
                else:
                    debug_info['db_operations'].append({
                        'operation': 'save_failed_final',
                        'timestamp': time.time(),
                        'error': 'Max retries exceeded',
                        'final_error': str(save_error)
                    })
                    logger.error(f"💀 AI消息保存彻底失败，已达到最大重试次数: {ai_msg_id}")
            
            message_save_queue.task_done()
            
        except queue.Empty:
            # 队列超时是正常情况，不是异常，不需要记录错误日志
            # logger.debug("⏰ 消息保存队列超时，继续等待...")
            continue
        except Exception as worker_error:
            # 只有真正的异常才记录错误日志
            logger.error(f"💥 消息保存工作线程真实异常: {str(worker_error)}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            time.sleep(1)  # 避免循环错误

def start_message_save_worker():
    """启动消息保存工作线程"""
    global message_save_thread
    if message_save_thread is None or not message_save_thread.is_alive():
        message_save_thread = threading.Thread(target=save_message_worker, daemon=True)
        message_save_thread.start()
        logger.info("✅ 消息保存工作线程已启动")

def cleanup_old_conversations(user_id, max_conversations=10):
    """清理用户的旧对话，只保留最近的max_conversations组对话"""
    try:
        # 获取用户的所有对话，按更新时间倒序排列
        conversations = db.session.query(Conversation)\
            .filter_by(user_id=user_id, is_active=True)\
            .order_by(Conversation.updated_at.desc())\
            .all()
        
        # 如果超过限制数量，删除旧的对话
        if len(conversations) > max_conversations:
            conversations_to_delete = conversations[max_conversations:]
            
            for conv in conversations_to_delete:
                logger.info(f"删除旧对话: {conv.id} - {conv.title}")
                # 删除对话的所有消息
                db.session.query(Message).filter_by(conversation_id=conv.id).delete()
                # 删除对话
                db.session.delete(conv)
            
            db.session.commit()
            logger.info(f"已清理 {len(conversations_to_delete)} 个旧对话，保留最近 {max_conversations} 个对话")
            
    except Exception as e:
        logger.error(f"清理旧对话失败: {str(e)}")
        db.session.rollback()

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """聊天API - 使用LangChain管理上下文，独立线程保存消息"""
    try:
        # 确保消息保存工作线程运行
        start_message_save_worker()
        
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'message': '缺少消息内容'
            }), 400
        
        user_message = data['message'].strip()
        conversation_id = data.get('conversation_id')
        knowledge_base_id = data.get('knowledge_base_id')
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': '消息不能为空'
            }), 400
        
        # 获取或创建对话
        conversation = None
        is_new_conversation = False
        if conversation_id:
            conversation = Conversation.query.filter_by(
                id=conversation_id,
                user_id=current_user.id
            ).first()
        
        if not conversation:
            # 创建新对话前，先清理旧对话
            cleanup_old_conversations(current_user.id, max_conversations=10)
            
            # 创建新对话
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                title=user_message[:50] + ('...' if len(user_message) > 50 else ''),
                model_name='deepseek-chat'
            )
            db.session.add(conversation)
            db.session.flush()  # 获取ID
            is_new_conversation = True
        
        # 检查是否需要流式响应
        use_stream = request.args.get('stream', 'true').lower() == 'true'
        
        # 保存用户消息
        user_msg_id = str(uuid.uuid4())
        user_msg = Message(
            id=user_msg_id,
            conversation_id=conversation.id,
            role='user',
            content=user_message,
            token_count=len(user_message.split()),
            created_at=datetime.utcnow()
        )
        db.session.add(user_msg)
        
        # 使用LangChain上下文服务
        conversation_service = ConversationService()
        
        # 获取知识库上下文
        knowledge_context = None
        if knowledge_base_id:
            kb = KnowledgeBase.query.filter_by(
                id=knowledge_base_id,
                user_id=current_user.id
            ).first()
            if kb:
                knowledge_context = f"来自知识库 '{kb.name}' 的相关内容"
        
        if use_stream:
            # 立即提交用户消息
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
            @stream_with_context
            def generate_stream():
                ai_response = ""
                ai_msg_id = str(uuid.uuid4())
                debug_info = {
                    'conversation_id': conversation.id,
                    'user_message_id': user_msg_id,
                    'ai_message_id': ai_msg_id,
                    'langchain_enabled': conversation_service.langchain_enabled,
                    'processing_steps': [],
                    'context_info': {},
                    'timing': {},
                    'db_operations': [],
                    'stream_mode': True,
                    'user_id': current_user.id
                }
                
                try:
                    start_time = time.time()
                    
                    # 记录用户消息保存
                    debug_info['db_operations'].append({
                        'operation': 'user_message_saved',
                        'timestamp': start_time,
                        'user_msg_id': user_msg_id,
                        'conversation_id': conversation.id,
                        'message_content_length': len(user_message)
                    })
                    
                    # 🔥 修复BUG2：立即发送初始化消息，让用户知道正在处理
                    yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation.id, 'user_message_id': user_msg_id, 'ai_message_id': ai_msg_id, 'debug_info': debug_info})}\n\n"
                    
                    debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 开始处理用户消息")
                    
                    # 发送处理状态更新
                    yield f"data: {json.dumps({'type': 'processing', 'status': '正在处理中...'})}\n\n"
                    
                    if conversation_service.langchain_enabled and conversation_service.langchain_service:
                        # 使用LangChain进行对话处理
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 使用LangChain处理上下文")
                        
                        # 获取系统提示词
                        system_prompt = conversation_service.get_system_prompt(
                            context_summary=None,  # LangChain会自动处理摘要
                            knowledge_context=knowledge_context
                        )
                        
                        debug_info['system_prompt'] = system_prompt
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 系统提示词准备完成")
                        
                        # 获取LangChain上下文信息（用于调试）
                        context_info = conversation_service.langchain_service.get_conversation_context(conversation.id)
                        debug_info['context_info'] = context_info
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] LangChain上下文加载完成: {context_info.get('message_count', 0)} 条消息")
                        
                        # 🔥 重大修复：使用真正的流式输出而不是模拟
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 开始真正的流式输出")
                        
                        # 直接使用DeepSeek的流式API，不通过LangChain
                        service = get_deepseek_service()
                        
                        # 获取LangChain上下文信息（用于调试）
                        context_info = conversation_service.langchain_service.get_conversation_context(conversation.id)
                        debug_info['context_info'] = context_info
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] LangChain上下文加载完成: {context_info.get('message_count', 0)} 条消息")
                        
                        # 获取对话历史用于流式API
                        conversation_history, _ = conversation_service.get_optimized_context(conversation)
                        conversation_history = [msg for msg in conversation_history if msg.get('content') != user_message]
                        
                        # 使用真正的流式API
                        try:
                            for chunk in service.chat_stream(
                                user_message=user_message,
                                conversation_history=conversation_history,
                                knowledge_context=knowledge_context,
                                system_prompt=system_prompt
                            ):
                                ai_response += chunk
                                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                            
                            debug_info['langchain_result'] = {
                                'success': True,
                                'response_length': len(ai_response),
                                'context_info': context_info,
                                'stream_mode': True
                            }
                            
                        except Exception as stream_error:
                            # 流式输出失败，回退到非流式
                            logger.error(f"流式输出失败，回退到非流式: {stream_error}")
                            debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 流式输出失败，回退到非流式")
                            
                            try:
                                langchain_result = conversation_service.langchain_service.chat_with_langchain(
                                    conversation_id=conversation.id,
                                    user_message=user_message,
                                    system_prompt=system_prompt,
                                    knowledge_context=knowledge_context
                                )
                                
                                if langchain_result['success']:
                                    ai_response = langchain_result['response']
                                    # 快速发送响应
                                    chunk_size = 30
                                    for i in range(0, len(ai_response), chunk_size):
                                        chunk = ai_response[i:i + chunk_size]
                                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                                        time.sleep(0.005)  # 极短延迟
                                        
                                    debug_info['langchain_result'] = {
                                        'success': True,
                                        'response_length': len(ai_response),
                                        'context_info': context_info,
                                        'fallback_mode': True
                                    }
                                else:
                                    debug_info['langchain_result'] = {
                                        'success': False,
                                        'error': langchain_result.get('error', '未知错误')
                                    }
                                    ai_response = "抱歉，LangChain处理出现问题，请稍后重试。"
                                    yield f"data: {json.dumps({'type': 'content', 'content': ai_response})}\n\n"
                                    
                            except Exception as fallback_error:
                                logger.error(f"LangChain回退也失败: {fallback_error}")
                                debug_info['langchain_result'] = {
                                    'success': False,
                                    'error': f"流式和回退都失败: {str(fallback_error)}"
                                }
                                ai_response = "抱歉，处理出现问题，请稍后重试。"
                                yield f"data: {json.dumps({'type': 'content', 'content': ai_response})}\n\n"
                    
                    else:
                        # 回退到传统方式（如果LangChain未启用）
                        debug_info['processing_steps'].append(f"[{time.time() - start_time:.3f}s] 使用传统方式处理上下文")
                        
                        # 获取优化后的上下文
                        conversation_history, context_summary = conversation_service.get_optimized_context(conversation)
                        conversation_history = [msg for msg in conversation_history if msg.get('content') != user_message]
                        
                        debug_info['traditional_context'] = {
                            'history_count': len(conversation_history),
                            'has_summary': context_summary is not None
                        }
                        
                        system_prompt = conversation_service.get_system_prompt(
                            context_summary=context_summary,
                            knowledge_context=knowledge_context
                        )
                        
                        # 获取DeepSeek服务并流式获取响应
                        service = get_deepseek_service()
                        for chunk in service.chat_stream(
                            user_message=user_message,
                            conversation_history=conversation_history,
                            knowledge_context=knowledge_context,
                            system_prompt=system_prompt
                        ):
                            ai_response += chunk
                            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
                    # 完成处理
                    debug_info['timing']['total_time'] = time.time() - start_time
                    debug_info['processing_steps'].append(f"[{debug_info['timing']['total_time']:.3f}s] 对话处理完成，准备保存AI消息")
                    
                    # 🔥 关键改进：将AI消息保存任务加入独立线程队列
                    if ai_response.strip():  # 确保有有效响应
                        save_data = {
                            'conversation_id': conversation.id,
                            'ai_msg_id': ai_msg_id,
                            'ai_response': ai_response,
                            'debug_info': debug_info,
                            'user_id': current_user.id,
                            'retry_count': 0
                        }
                        
                        # 加入保存队列（异步处理）
                        message_save_queue.put(save_data)
                        
                        debug_info['processing_steps'].append(f"[{debug_info['timing']['total_time']:.3f}s] AI消息已加入保存队列")
                        debug_info['db_operations'].append({
                            'operation': 'ai_message_queued_for_save',
                            'timestamp': time.time(),
                            'ai_msg_id': ai_msg_id,
                            'response_length': len(ai_response),
                            'queue_size': message_save_queue.qsize()
                        })
                    else:
                        debug_info['processing_steps'].append(f"[{debug_info['timing']['total_time']:.3f}s] ⚠️ AI响应为空，跳过保存")
                    
                    debug_info['final_stats'] = {
                        'ai_response_length': len(ai_response),
                        'processing_complete': True,
                        'save_queued': bool(ai_response.strip()),
                        'queue_size': message_save_queue.qsize()
                    }
                    
                    # 发送完成消息，包含调试信息
                    yield f"data: {json.dumps({'type': 'done', 'message_id': ai_msg_id, 'full_response': ai_response, 'debug_info': debug_info})}\n\n"
                    
                except Exception as e:
                    logger.error(f"流式响应异常: {str(e)}")
                    debug_info['error'] = {
                        'message': str(e),
                        'type': type(e).__name__,
                        'traceback': traceback.format_exc(),
                        'occurred_at': time.time() - start_time if 'start_time' in locals() else 'unknown'
                    }
                    debug_info['db_operations'].append({
                        'operation': 'stream_error',
                        'timestamp': time.time(),
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'debug_info': debug_info})}\n\n"
            
            return Response(
                generate_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Cache-Control'
                }
            )
        
        else:
            # 非流式响应（使用LangChain）
            if conversation_service.langchain_enabled and conversation_service.langchain_service:
                system_prompt = conversation_service.get_system_prompt(
                    context_summary=None,
                    knowledge_context=knowledge_context
                )
                
                langchain_result = conversation_service.langchain_service.chat_with_langchain(
                    conversation_id=conversation.id,
                    user_message=user_message,
                    system_prompt=system_prompt,
                    knowledge_context=knowledge_context
                )
                
                if langchain_result['success']:
                    ai_response = langchain_result['response']
                else:
                    return jsonify({
                        'success': False,
                        'message': f"LangChain处理失败: {langchain_result.get('error', '未知错误')}"
                    }), 500
            else:
                # 回退到传统方式
                conversation_history, context_summary = conversation_service.get_optimized_context(conversation)
                conversation_history = [msg for msg in conversation_history if msg.get('content') != user_message]
                
                system_prompt = conversation_service.get_system_prompt(
                    context_summary=context_summary,
                    knowledge_context=knowledge_context
                )
                
                service = get_deepseek_service()
                api_result = service.chat_with_context(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    knowledge_context=knowledge_context,
                    system_prompt=system_prompt,
                    stream=False
                )
                
                if not api_result['success']:
                    return jsonify({
                        'success': False,
                        'message': f"AI服务调用失败: {api_result.get('error', '未知错误')}"
                    }), 500
                
                ai_response = api_result['data']['choices'][0]['message']['content']
            
            # 保存AI消息（非流式模式直接保存）
            ai_msg_id = str(uuid.uuid4())
            ai_msg = Message(
                id=ai_msg_id,
                conversation_id=conversation.id,
                role='assistant',
                content=ai_response,
                token_count=len(ai_response.split()),
                created_at=datetime.utcnow()
            )
            db.session.add(ai_msg)
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation.id,
                'message_id': ai_msg_id,
                'langchain_enabled': conversation_service.langchain_enabled
            })
            
    except Exception as e:
        logger.error(f"聊天API异常: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/chat_simple', methods=['POST'])
@login_required
def chat_simple():
    """简单聊天API（非流式）"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'message': '缺少消息内容'
            }), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': '消息不能为空'
            }), 400
        
        # 直接调用DeepSeek API进行测试
        service = get_deepseek_service()
        result = service.simple_chat(user_message)
        
        if result['success']:
            return jsonify({
                'success': True,
                'response': result['response'],
                'usage': result.get('usage', {})
            })
        else:
            return jsonify({
                'success': False,
                'message': f"AI服务调用失败: {result.get('error', '未知错误')}"
            }), 500
            
    except Exception as e:
        logger.error(f"简单聊天API异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@api_bp.route('/knowledge_bases', methods=['GET'])
@login_required
def get_knowledge_bases():
    """获取用户知识库列表"""
    try:
        knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'knowledge_bases': [kb.to_dict() for kb in knowledge_bases]
        })
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取知识库列表失败'
        }), 500

@api_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取对话列表"""
    try:
        # 只获取活跃的对话，按更新时间倒序排列（最新的在前）
        conversations = db.session.query(Conversation)\
            .filter_by(user_id=current_user.id, is_active=True)\
            .order_by(Conversation.updated_at.desc())\
            .all()
        
        conversation_list = []
        for conv in conversations:
            # 获取消息统计
            message_count = db.session.query(Message)\
                .filter_by(conversation_id=conv.id)\
                .count()
            
            # 获取最后一条消息的预览
            last_message = db.session.query(Message)\
                .filter_by(conversation_id=conv.id)\
                .order_by(Message.created_at.desc())\
                .first()
            
            last_message_preview = None
            last_message_time = None
            if last_message:
                # 截取消息内容的前50个字符作为预览
                preview_content = last_message.content[:50]
                if len(last_message.content) > 50:
                    preview_content += '...'
                last_message_preview = f"{'👤' if last_message.role == 'user' else '🤖'} {preview_content}"
                last_message_time = last_message.created_at.isoformat()
            
            conversation_list.append({
                'id': conv.id,
                'title': conv.title or '新对话',
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': message_count,
                'last_message_preview': last_message_preview,
                'last_message_time': last_message_time,
                'model_name': conv.model_name
            })
        
        return jsonify({
            'success': True,
            'conversations': conversation_list,
            'total_count': len(conversation_list)
        })
    
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取对话列表失败: {str(e)}'
        }), 500

@api_bp.route('/conversations/<conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    """获取对话的所有消息"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '对话不存在'
            }), 404
        
        # 强制刷新数据库连接，避免缓存问题
        db.session.expunge_all()
        
        # 按创建时间升序排列，确保消息按对话顺序显示
        messages = db.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.asc())\
            .all()
        
        logger.info(f"查询对话 {conversation_id} 的消息，共找到 {len(messages)} 条消息")
        for i, msg in enumerate(messages):
            logger.info(f"消息 {i+1}: ID={msg.id}, role={msg.role}, created_at={msg.created_at}, content={msg.content[:50]}...")
        
        message_list = []
        for i, msg in enumerate(messages):
            # 计算消息的相对时间差
            time_diff = None
            if i > 0:
                prev_msg = messages[i-1]
                diff_seconds = (msg.created_at - prev_msg.created_at).total_seconds()
                if diff_seconds > 60:  # 超过1分钟显示时间差
                    if diff_seconds < 3600:  # 小于1小时
                        time_diff = f"{int(diff_seconds // 60)}分钟后"
                    elif diff_seconds < 86400:  # 小于1天
                        time_diff = f"{int(diff_seconds // 3600)}小时后"
                    else:  # 超过1天
                        time_diff = f"{int(diff_seconds // 86400)}天后"
            
            message_list.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'token_count': msg.token_count or 0,
                'created_at': msg.created_at.isoformat(),
                'created_at_formatted': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'time_diff': time_diff,
                'sequence_number': i + 1  # 消息序号
            })
        
        return jsonify({
            'success': True,
            'messages': message_list,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'message_count': len(message_list),
                'model_name': conversation.model_name
            }
        })
    
    except Exception as e:
        logger.error(f"获取对话消息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取对话消息失败: {str(e)}'
        }), 500

@api_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """删除对话及其所有消息"""
    try:
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '对话不存在'
            }), 404
        
        # 删除对话的所有消息
        db.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .delete()
        
        # 删除对话
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '对话已删除'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除对话失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除对话失败: {str(e)}'
        }), 500

@api_bp.route('/conversations/<conversation_id>/title', methods=['PUT'])
@login_required
def update_conversation_title(conversation_id):
    """更新对话标题"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({
                'success': False,
                'message': '标题不能为空'
            }), 400
        
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '对话不存在'
            }), 404
        
        conversation.title = new_title
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '标题已更新'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新对话标题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新对话标题失败: {str(e)}'
        }), 500

@api_bp.route('/test_deepseek', methods=['GET'])
@login_required
def test_deepseek():
    """测试DeepSeek API连接"""
    try:
        service = get_deepseek_service()
        result = service.test_connection()
        return jsonify(result)
    except Exception as e:
        logger.error(f"测试DeepSeek API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """获取用户统计信息"""
    try:
        knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
        
        stats = {
            'knowledge_bases_count': len(knowledge_bases),
            'conversations_count': current_user.conversations.filter_by(is_active=True).count(),
            'total_documents': sum(kb.document_count for kb in knowledge_bases),
            'total_messages': sum(conv.message_count for conv in current_user.conversations),
            'total_storage_size': sum(kb.total_size for kb in knowledge_bases)
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取统计信息失败'
        }), 500

@api_bp.route('/save_message', methods=['POST'])
@login_required
def save_message():
    """保存AI响应消息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '缺少数据'}), 400
        
        conversation_id = data.get('conversation_id')
        message_id = data.get('message_id')
        content = data.get('content')
        role = data.get('role', 'assistant')
        
        if not all([conversation_id, message_id, content]):
            return jsonify({'success': False, 'message': '缺少必需字段'}), 400
        
        # 确保在应用上下文中进行数据库操作
        with current_app.app_context():
            # 验证对话所有权
            conversation = Conversation.query.filter_by(
                id=conversation_id,
                user_id=current_user.id
            ).first()
            
            if not conversation:
                return jsonify({'success': False, 'message': '对话不存在'}), 404
            
            # 检查消息是否已存在，避免重复保存
            existing_message = Message.query.filter_by(id=message_id).first()
            if existing_message:
                logger.info(f"消息 {message_id} 已存在，跳过保存")
                return jsonify({'success': True, 'message': '消息已存在'})
            
            # 保存消息
            message = Message(
                id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                token_count=0,
                created_at=datetime.utcnow()  # 明确设置创建时间
            )
            db.session.add(message)
            
            # 更新对话统计
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"前端备份保存消息成功: {message_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"保存消息失败: {str(e)}")
        try:
            with current_app.app_context():
                db.session.rollback()
        except:
            pass
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/test_context_summary', methods=['POST'])
@login_required
def test_context_summary():
    """测试上下文总结功能"""
    try:
        data = request.get_json()
        
        if not data or 'conversation_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺少对话ID'
            }), 400
        
        conversation_id = data['conversation_id']
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在'
            }), 404
        
        # 初始化对话服务
        conversation_service = ConversationService()
        
        # 获取优化后的上下文
        optimized_messages, context_summary = conversation_service.get_optimized_context(conversation)
        
        # 统计信息
        total_messages = conversation.messages.count()
        user_message_count = conversation_service.count_user_messages(conversation)
        should_summarize = conversation_service.should_summarize_context(conversation)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'total_messages': total_messages,
            'user_message_count': user_message_count,
            'optimized_message_count': len(optimized_messages),
            'should_summarize': should_summarize,
            'has_summary': context_summary is not None,
            'context_summary': context_summary,
            'optimized_messages': optimized_messages[-5:] if optimized_messages else []  # 只返回最后5条用于预览
        })
        
    except Exception as e:
        logger.error(f"测试上下文总结失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

@api_bp.route('/conversation_stats', methods=['GET'])
@login_required
def get_conversation_stats():
    """获取对话统计信息"""
    try:
        conversation_id = request.args.get('conversation_id')
        
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': '缺少对话ID'
            }), 400
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在'
            }), 404
        
        conversation_service = ConversationService()
        
        # 基础统计
        total_messages = conversation.messages.count()
        user_messages = conversation.messages.filter_by(role='user').count()
        ai_messages = conversation.messages.filter_by(role='assistant').count()
        
        # 上下文管理统计
        should_summarize = conversation_service.should_summarize_context(conversation)
        optimized_messages, has_summary = conversation_service.get_optimized_context(conversation)
        
        # LangChain 上下文分析
        context_analysis = conversation_service.get_context_analysis(conversation_id)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'stats': {
                'total_messages': total_messages,
                'user_messages': user_messages,
                'ai_messages': ai_messages,
                'should_summarize': should_summarize,
                'optimized_message_count': len(optimized_messages) if optimized_messages else 0,
                'has_context_summary': has_summary is not None,
                'summary_rounds_config': conversation_service.summary_rounds,
                'max_context_messages': conversation_service.max_context_messages,
                'langchain_enabled': conversation_service.langchain_enabled
            },
            'context_analysis': context_analysis
        })
        
    except Exception as e:
        logger.error(f"获取对话统计信息异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/langchain/context/<conversation_id>', methods=['GET'])
@login_required
def get_langchain_context(conversation_id):
    """获取 LangChain 管理的对话上下文"""
    try:
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在或无权限访问'
            }), 404
        
        conversation_service = ConversationService()
        
        if not conversation_service.langchain_enabled:
            return jsonify({
                'success': False,
                'message': 'LangChain 功能未启用'
            }), 400
        
        # 获取 LangChain 上下文信息
        context_info = conversation_service.langchain_service.get_conversation_context(conversation_id)
        
        return jsonify({
            'success': True,
            'context_info': context_info
        })
        
    except Exception as e:
        logger.error(f"获取 LangChain 上下文异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/langchain/summary/<conversation_id>', methods=['GET'])
@login_required
def get_langchain_summary(conversation_id):
    """获取 LangChain 生成的对话摘要"""
    try:
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在或无权限访问'
            }), 404
        
        conversation_service = ConversationService()
        
        if not conversation_service.langchain_enabled:
            return jsonify({
                'success': False,
                'message': 'LangChain 功能未启用'
            }), 400
        
        # 获取对话摘要
        summary = conversation_service.langchain_service.get_conversation_summary(conversation_id)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'summary': summary,
            'has_summary': summary is not None
        })
        
    except Exception as e:
        logger.error(f"获取 LangChain 摘要异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/langchain/analyze/<conversation_id>', methods=['GET'])
@login_required
def analyze_langchain_context(conversation_id):
    """分析 LangChain 管理的对话上下文"""
    try:
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在或无权限访问'
            }), 404
        
        conversation_service = ConversationService()
        
        # 获取上下文分析
        analysis = conversation_service.get_context_analysis(conversation_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"分析 LangChain 上下文异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/langchain/config', methods=['GET'])
@login_required
def get_langchain_config():
    """获取 LangChain 配置信息"""
    try:
        from config.settings import Config
        
        config_info = {
            'enabled': BaseConfig.LANGCHAIN_ENABLED,
            'memory_type': BaseConfig.LANGCHAIN_MEMORY_TYPE,
            'max_token_limit': BaseConfig.LANGCHAIN_MAX_TOKEN_LIMIT,
            'window_size': BaseConfig.LANGCHAIN_WINDOW_SIZE,
            'debug': BaseConfig.LANGCHAIN_DEBUG,
            'verbose': BaseConfig.LANGCHAIN_VERBOSE,
            'conversation_summary_rounds': BaseConfig.CONVERSATION_SUMMARY_ROUNDS,
            'max_context_messages': BaseConfig.MAX_CONTEXT_MESSAGES,
            'conversation_summary_token_limit': BaseConfig.CONVERSATION_SUMMARY_TOKEN_LIMIT
        }
        
        return jsonify({
            'success': True,
            'config': config_info
        })
        
    except Exception as e:
        logger.error(f"获取 LangChain 配置异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/langchain/test', methods=['POST'])
@login_required
def test_langchain_integration():
    """测试 LangChain 集成功能"""
    try:
        data = request.get_json()
        test_message = data.get('message', '你好，这是一个测试消息')
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': '缺少对话ID'
            }), 400
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话不存在或无权限访问'
            }), 404
        
        conversation_service = ConversationService()
        
        if not conversation_service.langchain_enabled:
            return jsonify({
                'success': False,
                'message': 'LangChain 功能未启用'
            }), 400
        
        # 使用 LangChain 进行测试对话
        result = conversation_service.langchain_service.chat_with_langchain(
            conversation_id=conversation_id,
            user_message=test_message,
            system_prompt="你是SuperRAG智能助手的测试模式。请简短回应用户的测试消息。"
        )
        
        return jsonify({
            'success': True,
            'test_result': result
        })
        
    except Exception as e:
        logger.error(f"测试 LangChain 集成异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@api_bp.route('/message_save_status', methods=['GET'])
@login_required
def get_message_save_status():
    """获取消息保存队列状态"""
    try:
        global message_save_thread, message_save_queue
        
        thread_status = "未启动"
        if message_save_thread:
            if message_save_thread.is_alive():
                thread_status = "运行中"
            else:
                thread_status = "已停止"
        
        status = {
            "queue_size": message_save_queue.qsize(),
            "thread_status": thread_status,
            "thread_id": message_save_thread.ident if message_save_thread else None,
            "thread_name": message_save_thread.name if message_save_thread else None,
            "queue_empty": message_save_queue.empty(),
            "current_time": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/test_multi_turn', methods=['POST'])
@login_required 
def test_multi_turn():
    """测试多轮对话功能"""
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({
                'success': False,
                'error': '缺少消息数据'
            }), 400
        
        messages = data['messages']
        conversation_id = data.get('conversation_id')
        
        # 获取对话服务
        conversation_service = ConversationService()
        
        responses = []
        for i, msg in enumerate(messages):
            user_message = msg.get('content', '')
            if not user_message:
                continue
                
            # 获取或创建对话
            conversation = None
            if conversation_id:
                conversation = Conversation.query.filter_by(
                    id=conversation_id,
                    user_id=current_user.id
                ).first()
            
            if not conversation:
                conversation = Conversation(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    title=f"测试对话 {datetime.now().strftime('%H:%M:%S')}",
                    model_name='deepseek-chat',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(conversation)
                db.session.commit()
                conversation_id = conversation.id
            
            # 保存用户消息
            user_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role='user',
                content=user_message,
                token_count=len(user_message.split()),
                created_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            
            # 获取AI响应
            context_summary = conversation_service.get_conversation_summary(conversation.id) if i > 0 else None
            system_prompt = conversation_service.get_system_prompt(
                context_summary=context_summary
            )
            
            service = get_deepseek_service()
            api_result = service.chat_with_context(
                user_message=user_message,
                conversation_history=[],
                system_prompt=system_prompt
            )
            
            if api_result['success']:
                ai_response = api_result['data']['choices'][0]['message']['content']
                
                # 保存AI消息
                ai_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role='assistant',
                    content=ai_response,
                    token_count=len(ai_response.split()),
                    created_at=datetime.utcnow()
                )
                db.session.add(ai_msg)
                
                # 更新对话
                conversation.message_count += 2
                conversation.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                responses.append({
                    'round': i + 1,
                    'user_message': user_message,
                    'ai_response': ai_response,
                    'success': True
                })
            else:
                responses.append({
                    'round': i + 1,
                    'user_message': user_message,
                    'error': api_result['error'],
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'responses': responses,
            'total_rounds': len(responses)
        })
        
    except Exception as e:
        logger.error(f"多轮对话测试失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/conversation_database_info/<conversation_id>', methods=['GET'])
@login_required
def get_conversation_database_info(conversation_id):
    """获取对话的完整数据库信息，用于调试页面可视化"""
    try:
        # 验证对话权限
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': '对话不存在或无权限访问'
            }), 404
        
        # 获取对话详细信息
        conversation_info = {
            'id': conversation.id,
            'title': conversation.title,
            'user_id': conversation.user_id,
            'knowledge_base_id': conversation.knowledge_base_id,
            'model_name': conversation.model_name,
            'system_prompt': conversation.system_prompt,
            'temperature': conversation.temperature,
            'max_tokens': conversation.max_tokens,
            'message_count': conversation.message_count,
            'total_tokens': conversation.total_tokens,
            'is_active': conversation.is_active,
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
            'created_at_formatted': conversation.created_at.strftime('%Y-%m-%d %H:%M:%S') if conversation.created_at else None,
            'updated_at_formatted': conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S') if conversation.updated_at else None
        }
        
        # 获取所有消息的详细信息
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.asc()).all()
        
        messages_info = []
        for i, msg in enumerate(messages):
            msg_info = {
                'sequence': i + 1,
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'role': msg.role,
                'content': msg.content,
                'content_length': len(msg.content),
                'content_preview': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                'token_count': msg.token_count,
                'used_knowledge_base': msg.used_knowledge_base,
                'relevant_chunks': msg.relevant_chunks,
                'msg_metadata': msg.msg_metadata,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'created_at_formatted': msg.created_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if msg.created_at else None,
                'updated_at': None,
                'updated_at_formatted': None,
            }
            
            # 计算与前一条消息的时间差
            if i > 0:
                prev_msg = messages[i-1]
                if msg.created_at and prev_msg.created_at:
                    time_diff = (msg.created_at - prev_msg.created_at).total_seconds()
                    msg_info['time_diff_seconds'] = round(time_diff, 3)
                    msg_info['time_diff_formatted'] = f"{time_diff:.3f}s"
            
            messages_info.append(msg_info)
        
        # 统计信息
        user_messages = [m for m in messages if m.role == 'user']
        ai_messages = [m for m in messages if m.role == 'assistant']
        system_messages = [m for m in messages if m.role == 'system']
        
        statistics = {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'ai_messages': len(ai_messages),
            'system_messages': len(system_messages),
            'total_characters': sum(len(m.content) for m in messages),
            'total_tokens': sum(m.token_count or 0 for m in messages),
            'avg_message_length': round(sum(len(m.content) for m in messages) / len(messages), 2) if messages else 0,
            'conversation_duration': None,
            'conversation_duration_formatted': None
        }
        
        # 计算对话持续时间
        if messages and len(messages) > 1:
            first_msg = messages[0]
            last_msg = messages[-1]
            if first_msg.created_at and last_msg.created_at:
                duration = (last_msg.created_at - first_msg.created_at).total_seconds()
                statistics['conversation_duration'] = duration
                if duration < 60:
                    statistics['conversation_duration_formatted'] = f"{duration:.1f}秒"
                elif duration < 3600:
                    statistics['conversation_duration_formatted'] = f"{duration/60:.1f}分钟"
                else:
                    statistics['conversation_duration_formatted'] = f"{duration/3600:.1f}小时"
        
        # 数据库表信息
        table_info = {
            'conversation_table': 'conversations',
            'message_table': 'messages',
            'user_table': 'users',
            'indexes': [
                'conversations.user_id',
                'conversations.created_at',
                'messages.conversation_id',
                'messages.created_at',
                'messages.role'
            ]
        }
        
        # 获取用户信息
        user_info = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'created_at_formatted': current_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if current_user.created_at else None
        }
        
        # 查询相关统计
        query_stats = {
            'user_total_conversations': Conversation.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).count(),
            'user_total_messages': db.session.query(Message)\
                .join(Conversation)\
                .filter(Conversation.user_id == current_user.id)\
                .count(),
            'database_total_conversations': Conversation.query.filter_by(is_active=True).count(),
            'database_total_messages': Message.query.count(),
            'database_total_users': db.session.query(db.func.count(db.distinct(Conversation.user_id))).scalar()
        }
        
        return jsonify({
            'success': True,
            'conversation': conversation_info,
            'messages': messages_info,
            'statistics': statistics,
            'table_info': table_info,
            'user_info': user_info,
            'query_stats': query_stats,
            'retrieved_at': datetime.utcnow().isoformat(),
            'retrieved_at_formatted': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"获取对话数据库信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@api_bp.route('/database_search', methods=['GET'])
@login_required
def database_search():
    """数据库搜索功能 - 支持对话ID和关键词搜索"""
    try:
        # 获取搜索参数
        search_query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'keyword')  # keyword, conversation_id, all
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not search_query:
            return jsonify({
                'success': False,
                'error': '搜索关键词不能为空'
            }), 400
        
        results = {
            'query': search_query,
            'search_type': search_type,
            'conversations': [],
            'messages': [],
            'total_conversations': 0,
            'total_messages': 0,
            'page': page,
            'per_page': per_page
        }
        
        # 基础查询：只显示当前用户的数据
        base_conversation_query = Conversation.query.filter_by(
            user_id=current_user.id,
            is_active=True
        )
        
        base_message_query = db.session.query(Message)\
            .join(Conversation)\
            .filter(Conversation.user_id == current_user.id)
        
        if search_type == 'conversation_id' or search_type == 'all':
            # 搜索对话ID（支持部分匹配）
            conversation_results = base_conversation_query\
                .filter(Conversation.id.contains(search_query))\
                .order_by(Conversation.updated_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
            
            for conv in conversation_results.items:
                # 获取该对话的消息
                conv_messages = Message.query.filter_by(conversation_id=conv.id)\
                    .order_by(Message.created_at.asc()).all()
                
                results['conversations'].append({
                    'id': conv.id,
                    'title': conv.title,
                    'message_count': len(conv_messages),
                    'created_at_formatted': conv.created_at.strftime('%Y-%m-%d %H:%M:%S') if conv.created_at else None,
                    'updated_at_formatted': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S') if conv.updated_at else None,
                    'messages': [{
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content,
                        'content_length': len(msg.content),
                        'created_at_formatted': msg.created_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if msg.created_at else None,
                        'token_count': msg.token_count
                    } for msg in conv_messages]
                })
            
            results['total_conversations'] = conversation_results.total
        
        if search_type == 'keyword' or search_type == 'all':
            # 关键词搜索
            keyword_conversations = base_conversation_query\
                .filter(db.or_(
                    Conversation.title.contains(search_query),
                    Conversation.system_prompt.contains(search_query)
                ))\
                .order_by(Conversation.updated_at.desc())\
                .all()
            
            # 搜索消息内容
            keyword_messages = base_message_query\
                .filter(Message.content.contains(search_query))\
                .order_by(Message.created_at.desc())\
                .limit(per_page * 3)\
                .all()  # 限制消息结果数量
            
            # 处理对话搜索结果
            for conv in keyword_conversations:
                if not any(c['id'] == conv.id for c in results['conversations']):
                    # 获取匹配的消息
                    matching_messages = [msg for msg in keyword_messages if msg.conversation_id == conv.id]
                    
                    results['conversations'].append({
                        'id': conv.id,
                        'title': conv.title,
                        'match_type': '标题匹配' if search_query in conv.title else '系统提示词匹配',
                        'message_count': conv.message_count,
                        'created_at_formatted': conv.created_at.strftime('%Y-%m-%d %H:%M:%S') if conv.created_at else None,
                        'updated_at_formatted': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S') if conv.updated_at else None,
                        'matching_messages_count': len(matching_messages)
                    })
            
            # 处理消息搜索结果
            message_groups = {}
            for msg in keyword_messages:
                conv_id = msg.conversation_id
                if conv_id not in message_groups:
                    conversation = Conversation.query.get(conv_id)
                    message_groups[conv_id] = {
                        'conversation_id': conv_id,
                        'conversation_title': conversation.title if conversation else '未知对话',
                        'messages': []
                    }
                
                message_groups[conv_id]['messages'].append({
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'content_length': len(msg.content),
                    'content_preview': msg.content[:200] + '...' if len(msg.content) > 200 else msg.content,
                    'created_at_formatted': msg.created_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if msg.created_at else None,
                    'token_count': msg.token_count,
                    'highlight_query': search_query  # 用于前端高亮
                })
            
            results['messages'] = list(message_groups.values())
            results['total_messages'] = len(keyword_messages)
        
        # 搜索统计
        results['search_stats'] = {
            'conversations_found': len(results['conversations']),
            'message_groups_found': len(results['messages']),
            'total_message_matches': sum(len(group['messages']) for group in results['messages']),
            'search_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"数据库搜索失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500 