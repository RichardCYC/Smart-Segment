import Layout from '@/components/Layout';
import SEO from '@/components/SEO';
import { getAllArticles } from '@/lib/articles';
import { Card, CardActionArea, CardContent, Container, Grid, Typography } from '@mui/material';
import { format } from 'date-fns';
import { GetStaticProps } from 'next';
import Link from 'next/link';

interface Article {
  slug: string;
  title: string;
  description: string;
  publishedAt: string;
}

interface ArticlesPageProps {
  articles: Article[];
}

export default function ArticlesPage({ articles }: ArticlesPageProps) {
  return (
    <Layout>
      <SEO
        title="Articles | Smart Segments"
        description="Explore our collection of articles about data segmentation, analytics, and best practices."
        canonical="/articles"
      />

      <Container maxWidth="lg">
        <Typography variant="h3" component="h1" gutterBottom>
          Articles
        </Typography>

        <Grid container spacing={4}>
          {articles.map((article) => (
            <Grid item xs={12} md={6} key={article.slug}>
              <Card>
                <CardActionArea component={Link} href={`/articles/${article.slug}`}>
                  <CardContent>
                    <Typography variant="h5" component="h2" gutterBottom>
                      {article.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {format(new Date(article.publishedAt), 'MMMM d, yyyy')}
                    </Typography>
                    <Typography variant="body1">
                      {article.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Layout>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  const articles = await getAllArticles();

  return {
    props: {
      articles,
    },
    revalidate: 3600, // Revalidate every hour
  };
};