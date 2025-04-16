import {
    Box,
    Button,
    CircularProgress,
    TextField
} from '@mui/material';
import axios from 'axios';
import { useState } from 'react';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const [isLoading, setLoading] = useState(false); // loader state
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        } finally {
            setLoading(false);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <TextField
                    label="Loaded Data"
                    value={loadedData || ''}
                    sx={{ mt: 2 }}
                    InputLabelProps={{ shrink: true }}
                    disabled
                />
                <Button
                    onClick={handleLoad}
                    sx={{ mt: 2 }}
                    variant='contained'
                    disabled={isLoading}
                >
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Load Data'}
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{ mt: 1 }}
                    variant='contained'
                    disabled={isLoading}
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
