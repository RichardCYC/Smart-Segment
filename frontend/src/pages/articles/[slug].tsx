import Layout from '@/components/Layout';
import SEO from '@/components/SEO';
import { Article, getAllArticles, getArticleBySlug } from '@/lib/articles';
import { Box, Container, Typography } from '@mui/material';
import { format } from 'date-fns';
import { GetStaticPaths, GetStaticProps } from 'next';

interface ArticlePageProps {
  article: Article;
}

export default function ArticlePage({ article }: ArticlePageProps) {
  return (
    <Layout>
      <SEO
        title={`${article.title} | Smart Segments`}
        description={article.description}
        ogType="article"
      />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            {article.title}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            {format(new Date(article.publishedAt), 'MMMM d, yyyy')} • {article.author}
          </Typography>
          <Box sx={{ mt: 4 }}>
            <div dangerouslySetInnerHTML={{ __html: article.content }} />
          </Box>
        </Box>
      </Container>
    </Layout>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const articles = await getAllArticles();
  const paths = articles.map((article) => ({
    params: { slug: article.slug },
  }));

  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps<ArticlePageProps> = async ({ params }) => {
  if (!params?.slug || typeof params.slug !== 'string') {
    return {
      notFound: true,
    };
  }

  const article = await getArticleBySlug(params.slug);

  return {
    props: {
      article,
    },
  };
};