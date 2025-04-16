// airtable.js

import {
    Box,
    Button,
    CircularProgress
} from '@mui/material';
import axios from 'axios';
import { useEffect, useState } from 'react';

export const HubspotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    // Function to open OAuth in a new window
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/authorize`, formData);  //  TODO: Store URL hosts in constants (.env)
            const authURL = response?.data;

            const newWindow = window.open(authURL, 'Hubspot Authorization', 'width=600, height=600');

            // Polling for the window to close
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) {
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    // Function to handle logic when the OAuth window closes
    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/credentials`, formData); //  TODO: Store URL hosts in constants (.env)
            const credentials = response.data;
            console.log(credentials)
            if (credentials) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'Hubspot' }));
            }
            setIsConnecting(false);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    useEffect(() => {
        setIsConnected(integrationParams?.credentials ? true : false)
    }, []);

    return (
        <>
            <Box sx={{ mt: 2 }}>
                Parameters
                <Box display='flex' alignItems='center' justifyContent='center' sx={{ mt: 2 }}>
                    <Button
                        variant='contained'
                        onClick={isConnected ? () => { } : handleConnectClick}
                        color={isConnected ? 'success' : 'primary'}
                        disabled={isConnecting}
                        style={{
                            pointerEvents: isConnected ? 'none' : 'auto',
                            cursor: isConnected ? 'default' : 'pointer',
                            opacity: isConnected ? 1 : undefined
                        }}
                    >
                        {isConnected ? 'Hubspot Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to Hubspot'}
                    </Button>
                </Box>
            </Box>
        </>
    );
}
