"""
REST API 模块
"""
from typing import Dict, List, Optional
from flask import Blueprint, request, jsonify
import json


def create_api(app, research_engine) -> Blueprint:
    """
    创建 REST API 蓝图
    
    Args:
        app: Flask 应用
        research_engine: 研究引擎实例
        
    Returns:
        Blueprint: API 蓝图
    """
    api = Blueprint("api", __name__, url_prefix="/api")
    
    @api.route("/query", methods=["POST"])
    def submit_query():
        """
        提交研究问题
        
        Request JSON:
            query: str - 研究问题
            context: str (可选) - 背景信息
            
        Response:
            query_id: str - 查询 ID
            status: str - 处理状态
        """
        try:
            data = request.get_json()
            query = data.get("query", "")
            context = data.get("context")
            
            if not query:
                return jsonify({"error": "Query is required"}), 400
            
            # 处理查询
            query_id = research_engine.process_query(query, context)
            
            return jsonify({
                "query_id": query_id,
                "status": "processing",
            }), 202
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/results/<query_id>", methods=["GET"])
    def get_results(query_id: str):
        """
        获取查询结果
        
        Response:
            papers: List - 检索到的论文
            synthesis: Dict - 综合总结
            status: str - 处理状态
        """
        try:
            results = research_engine.get_results(query_id)
            
            if not results:
                return jsonify({"error": "Query not found"}), 404
            
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/papers", methods=["GET"])
    def list_papers():
        """
        获取所有论文
        
        Query Parameters:
            query_id: str (可选) - 查询 ID
            
        Response:
            papers: List - 论文列表
        """
        try:
            query_id = request.args.get("query_id")
            papers = research_engine.get_papers(query_id)
            
            return jsonify({
                "papers": [p.to_dict() if hasattr(p, 'to_dict') else p for p in papers]
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/papers", methods=["POST"])
    def add_paper():
        """
        手动添加论文
        
        Request JSON:
            paper: Dict - 论文信息
            query_id: str (可选) - 关联的查询 ID
            
        Response:
            paper_id: str - 论文 ID
        """
        try:
            data = request.get_json()
            paper = data.get("paper", {})
            query_id = data.get("query_id")
            
            if not paper or not paper.get("title"):
                return jsonify({"error": "Paper title is required"}), 400
            
            paper_id = research_engine.add_paper(paper, query_id)
            
            return jsonify({
                "paper_id": paper_id,
                "status": "added",
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/papers/<paper_id>", methods=["PUT"])
    def update_paper(paper_id: str):
        """
        更新论文信息
        
        Request JSON:
            paper: Dict - 更新的论文信息
            
        Response:
            status: str - 更新状态
        """
        try:
            data = request.get_json()
            paper = data.get("paper", {})
            
            research_engine.update_paper(paper_id, paper)
            
            return jsonify({"status": "updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/papers/<paper_id>", methods=["DELETE"])
    def delete_paper(paper_id: str):
        """
        删除论文
        
        Response:
            status: str - 删除状态
        """
        try:
            research_engine.delete_paper(paper_id)
            
            return jsonify({"status": "deleted"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/summary/<query_id>", methods=["GET"])
    def get_summary(query_id: str):
        """
        获取综合总结
        
        Response:
            summary: Dict - 综合总结
        """
        try:
            summary = research_engine.get_summary(query_id)
            
            if not summary:
                return jsonify({"error": "Summary not found"}), 404
            
            return jsonify(summary), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return api
