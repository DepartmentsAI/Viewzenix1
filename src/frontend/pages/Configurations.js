import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  FormControl, 
  FormControlLabel, 
  FormGroup, 
  TextField, 
  Switch, 
  Button,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function Configurations() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Webhook Configurations
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Webhook Settings
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Webhook URL"
                  variant="outlined"
                  defaultValue="https://api.example.com/webhook"
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Secret Key"
                  variant="outlined"
                  type="password"
                  defaultValue="your-secret-key"
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 2 }}>
              <Button variant="contained" color="primary">
                Update Webhook
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Order Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Base Order Percentage"
                    type="number"
                    defaultValue="0.02"
                    InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    margin="normal"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Limit Offset Ticks"
                    type="number"
                    defaultValue="0"
                    InputProps={{ inputProps: { step: 1 } }}
                    margin="normal"
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <FormGroup>
                    <FormControlLabel 
                      control={<Switch />} 
                      label="Use Limit Orders" 
                    />
                    <FormControlLabel 
                      control={<Switch />} 
                      label="Use Strategy Order Price" 
                    />
                  </FormGroup>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
        
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Stop Loss / Take Profit Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormGroup>
                    <FormControlLabel 
                      control={<Switch />} 
                      label="Attach SL/TP to Orders" 
                    />
                    <FormControlLabel 
                      control={<Switch />} 
                      label="Use Average Fill for SL/TP" 
                    />
                  </FormGroup>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Stop Loss Percentage"
                    type="number"
                    defaultValue="0.01"
                    InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    margin="normal"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Take Profit Percentage"
                    type="number"
                    defaultValue="0.02"
                    InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    margin="normal"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
        
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Global SL/TP Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormGroup>
                    <FormControlLabel 
                      control={<Switch />} 
                      label="Enable Global SL/TP" 
                    />
                  </FormGroup>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Base Equity"
                    type="number"
                    defaultValue="100000"
                    InputProps={{ inputProps: { min: 0 } }}
                    margin="normal"
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Global SL Percentage"
                    type="number"
                    defaultValue="0.80"
                    InputProps={{ inputProps: { min: 0, max: 1, step: 0.01 } }}
                    margin="normal"
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Global TP Percentage"
                    type="number"
                    defaultValue="1.20"
                    InputProps={{ inputProps: { min: 1, step: 0.01 } }}
                    margin="normal"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
        
        <Grid item xs={12} sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined">
              Reset to Defaults
            </Button>
            <Button variant="contained" color="primary">
              Save Configuration
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Configurations; 