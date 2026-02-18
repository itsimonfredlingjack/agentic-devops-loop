"""
Routes for news article presentation.
"""

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.business.news_service import ValidationError

news_bp = Blueprint("news", __name__)


def get_news_service():
    """Get NewsService from app config."""
    return current_app.config["news_service"]


@news_bp.route("/")
def index():
    """Display list of all news articles."""
    service = get_news_service()
    articles = service.get_all_articles()
    return render_template("index.html", articles=articles)


@news_bp.route("/article/new", methods=["GET", "POST"])
def new_article():
    """Display form and handle article creation."""
    if request.method == "GET":
        return render_template("article_form.html")

    # POST - create article
    service = get_news_service()

    try:
        service.create_article(
            title=request.form.get("title", ""),
            content=request.form.get("content", ""),
            author=request.form.get("author", ""),
            category=request.form.get("category"),
        )
        return redirect(url_for("news.index"))
    except ValidationError as e:
        return render_template("article_form.html", error=str(e)), 400


@news_bp.route("/article/<int:article_id>")
def article_detail(article_id):
    """Display single article details."""
    service = get_news_service()
    article = service.get_article_by_id(article_id)

    if article is None:
        return render_template("404.html"), 404

    return render_template("article_detail.html", article=article)
