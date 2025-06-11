import Layout from '@/components/Layout';
import SEO from '@/components/SEO';
import { getAllArticles, getArticleBySlug } from '@/lib/articles';
import { Box, Container, Typography } from '@mui/material';
import { format } from 'date-fns';
import { GetStaticPaths, GetStaticProps } from 'next';

interface Article {
  slug: string;
  title: string;
  description: string;
  content: string;
  publishedAt: string;
  author: string;
  tags: string[];
}

interface ArticlePageProps {
  article: Article;
}

export default function ArticlePage({ article }: ArticlePageProps) {
  return (
    <Layout>
      <SEO
        title={`${article.title} | Smart Segments`}
        description={article.description}
        canonical={`