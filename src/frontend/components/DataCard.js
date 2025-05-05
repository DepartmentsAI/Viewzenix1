import React from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  Box, 
  IconButton, 
  Divider,
  useTheme,
  Skeleton,
  Tooltip
} from '@mui/material';
import { MoreVert as MoreIcon, Refresh as RefreshIcon } from '@mui/icons-material';

/**
 * Reusable DataCard component for displaying summary information with consistent styling
 * 
 * @param {string} title - Card title
 * @param {React.ReactNode} icon - Icon to display
 * @param {React.ReactNode} children - Card content
 * @param {boolean} loading - Whether the card is in loading state
 * @param {function} onRefresh - Function to call when refresh button is clicked
 * @param {function} onMore - Function to call when more button is clicked
 * @param {object} sx - Additional styles to apply to the card
 */
const DataCard = ({ 
  title, 
  icon, 
  children, 
  loading = false,
  onRefresh,
  onMore,
  sx = {} 
}) => {
  const theme = useTheme();

  return (
    <Card 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        ...sx 
      }}
      elevation={2}
    >
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {icon && (
              <Box 
                sx={{ 
                  mr: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  color: theme.palette.primary.main
                }}
              >
                {icon}
              </Box>
            )}
            <Typography variant="h6" component="div">
              {title}
            </Typography>
          </Box>
        }
        action={
          <Box>
            {onRefresh && (
              <Tooltip title="Refresh">
                <IconButton aria-label="refresh" onClick={onRefresh} size="small">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            )}
            {onMore && (
              <Tooltip title="More options">
                <IconButton aria-label="more options" onClick={onMore} size="small">
                  <MoreIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        }
      />
      <Divider />
      <CardContent sx={{ flexGrow: 1, py: 2 }}>
        {loading ? (
          <>
            <Skeleton variant="text" height={30} width="80%" />
            <Skeleton variant="text" height={20} width="60%" />
            <Skeleton variant="text" height={20} width="70%" />
          </>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
};

export default DataCard; 