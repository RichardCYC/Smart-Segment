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
        title={`${article.title} | Smart Segment`}
        description={article.description}
        canonical={`/articles/${article.slug}`}
        ogType="article"
      />

      <Container maxWidth="md">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            {article.title}
          </Typography>

          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            By {article.author} • {format(new Date(article.publishedAt), 'MMMM d, yyyy')}
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
            {article.tags.map((tag) => (
              <Typography
                key={tag}
                variant="body2"
                sx={{
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                }}
              >
                {tag}
              </Typography>
            ))}
          </Box>
        </Box>

        <Box
          sx={{
            '& h2': { mt: 4, mb: 2 },
            '& p': { mb: 2 },
            '& ul, & ol': { mb: 2, pl: 3 },
            '& li': { mb: 1 },
          }}
          dangerouslySetInnerHTML={{ __html: article.content }}
        />
      </Container>
    </Layout>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const articles = await getAllArticles();

  return {
    paths: articles.map((article) => ({
      params: { slug: article.slug },
    })),
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const article = await getArticleBySlug(params?.slug as string);

  if (!article) {
    return {
      notFound: true,
    };
  }

  return {
    props: {
      article,
    },
    revalidate: 3600, // Revalidate every hour
  };
};