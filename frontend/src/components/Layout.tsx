import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();

  const isActive = (path: string) => {
    return router.pathname === path;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link href="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              Smart Segments
            </Link>
          </Typography>
          <Button
            color="inherit"
            component={Link}
            href="/"
            sx={{
              mr: 2,
              fontWeight: isActive('/') ? 'bold' : 'normal',
              borderBottom: isActive('/') ? '2px solid white' : 'none'
            }}
          >
            Home
          </Button>
          <Button
            color="inherit"
            component={Link}
            href="/articles"
            sx={{
              fontWeight: isActive('/articles') ? 'bold' : 'normal',
              borderBottom: isActive('/articles') ? '2px solid white' : 'none'
            }}
          >
            Articles
          </Button>
        </Toolbar>
      </AppBar>

      <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Container>

      <Box component="footer" sx={{ py: 3, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} Smart Segments. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}