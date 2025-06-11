import fs from 'fs';
import matter from 'gray-matter';
import path from 'path';
import { remark } from 'remark';
import html from 'remark-html';

const articlesDirectory = path.join(process.cwd(), 'content/articles');

export interface Article {
  slug: string;
  title: string;
  description: string;
  content: string;
  publishedAt: string;
  author: string;
  tags: string[];
}

export async function getAllArticles(): Promise<Omit<Article, 'content'>[]> {
  const fileNames = fs.readdirSync(articlesDirectory);
  const articles = await Promise.all(
    fileNames.map(async (fileName) => {
      const slug = fileName.replace(/\.md$/, '');
      const article = await getArticleBySlug(slug);
      const { content, ...articleWithoutContent } = article;
      return articleWithoutContent;
    })
  );

  return articles.sort((a, b) =>
    new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  );
}

export async function getArticleBySlug(slug: string): Promise<Article> {
  const fullPath = path.join(articlesDirectory, `${slug}.md`);
  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const { data, content } = matter(fileContents);

  const processedContent = await remark()
    .use(html)
    .process(content);

  return {
    slug,
    title: data.title,
    description: data.description,
    content: processedContent.toString(),
    publishedAt: data.publishedAt,
    author: data.author,
    tags: data.tags || [],
  };
}