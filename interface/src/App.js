import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

import withStyles from "@material-ui/core/styles/withStyles";
import {
    Card, CardContent, FormControl, FormHelperText,
    InputLabel, MenuItem, Select, Typography
} from "@material-ui/core";
import { callDalleService } from "./backend_api";
import GeneratedImageList from "./GeneratedImageList";
import TextPromptInput from "./TextPromptInput";

import "./App.css";
import BackendUrlInput from "./BackendUrlInput";
import LoadingSpinner from "./LoadingSpinner";
import NotificationCheckbox from './NotificationCheckbox';

const useStyles = () => ({
    root: {
        display: 'flex',
        width: '100%',
        flexDirection: 'column',
        margin: '60px 0px 60px 0px',
        alignItems: 'center',
        textAlign: 'center',
    },
    title: {
        marginBottom: '20px',
    },
    playgroundSection: {
        display: 'flex',
        flex: 1,
        width: '100%',
        alignItems: 'flex-start',
        justifyContent: 'center',
        marginTop: '20px',
    },
    settingsSection: {
        display: 'flex',
        flexDirection: 'column',
        padding: '1em',
        maxWidth: '300px',
    },
    searchQueryCard: {
        marginBottom: '20px'
    },
    imagesPerQueryControl: {
        marginTop: '20px',
    },
    formControl: {
        margin: "20px",
        minWidth: 120,
    },
    gallery: {
        display: 'flex',
        flex: '1',
        maxWidth: '50%',
        height: '100%',
        justifyContent: 'center',
        alignItems: 'flex-start',
        padding: '1rem',
    },
});

const NOTIFICATION_ICON = "https://camo.githubusercontent.com/95d3eed25e464b300d56e93644a26c8236a19e04572cf83a95c9d68f8126be83/68747470733a2f2f656d6f6a6970656469612d75732e73332e6475616c737461636b2e75732d776573742d312e616d617a6f6e6177732e636f6d2f7468756d62732f3234302f6170706c652f3238352f776f6d616e2d6172746973745f31663436392d323030642d31663361382e706e67";

const socketBackend = "35.184.104.157"
const socket = io("ws://" + socketBackend + ":8080", {transports: ['websocket']})

const App = ({ classes }) => {

    const [backendUrl, setBackendUrl] = useState('');
    const [promptText, setPromptText] = useState('');
    const [isFetchingImgs, setIsFetchingImgs] = useState(false);
    const [isCheckingBackendEndpoint, setIsCheckingBackendEndpoint] = useState(false);
    const [isValidBackendEndpoint, setIsValidBackendEndpoint] = useState(true);
    const [notificationsOn, setNotificationsOn] = useState(false);

    const [generatedImages, setGeneratedImages] = useState([]);
    const [generatedImagesFormat, setGeneratedImagesFormat] = useState('jpeg');

    const [apiError, setApiError] = useState('')
    const [imagesPerQuery, setImagesPerQuery] = useState(2);
    const [queryTime, setQueryTime] = useState(0);

    const imagesPerQueryOptions = 10
    const validBackendUrl = isValidBackendEndpoint && backendUrl

//    const socket = io("ws://" + backendUrl.replace("http://", "").replace("https://", ""));
    const [isSocketConnected, setIsSocketConnected] = useState("");
    const [socketIds, setSocketIds] = useState("");
    const [generateComplete, setGenerateComplete] = useState(0);

    useEffect(() => {
        socket.on('connect', () => {
          setIsSocketConnected("true")
          setSocketIds(socketIds + ", " + socket.id)
        });

        socket.on('disconnect', () => {
          console.log("Socket" + socket.id + "disconnected")
          setIsSocketConnected("false")
        });

        socket.on('generate_complete', (response) => {
            setGenerateComplete(generateComplete + 1)
            console.log("generate complete!")
            console.log(response)
            //setQueryTime(response['execution_time'])
            setGeneratedImages(response['data']['b64_images'])
            setGeneratedImagesFormat(response['data']['image_format'])
            setIsFetchingImgs(false)
        });

        return () => {
            socket.off('connect')
            socket.off('disconnect')
            socket.off('generate_complete')
            socket.close()
        }
    //from: https://socket.io/how-to/use-with-react-hooks
    //the 2nd argument of the useEffect() method must be [], or else the hook will be triggered every time a new message arrives
    }, [])

    function callModel(connectedSocketId) {
        setApiError('')
        setIsFetchingImgs(false)//TODO: true
        callDalleService(backendUrl, promptText, imagesPerQuery, connectedSocketId).then((response) => {
            console.log("Successful http call")
            console.log(response)
        }).catch((error) => {
            console.log('Error querying DALL-E service.', error)

            if (error.message === 'Timeout') {
                setApiError('Timeout querying DALL-E service (>1min). Consider reducing the images per query or use a stronger backend.')
            } else {
                setApiError('Error querying DALL-E service. Check your backend server logs.')
            }
            setIsFetchingImgs(false)
        })
    }

    function enterPressedCallback(promptText) {
        console.log('API call to DALL-E web service with the following prompt [' + promptText + ']');
        console.log("v7")
        callModel(socket.id)
    }

    function getGalleryContent() {
        if (apiError) {
            return <Typography variant="h5" color="error">{apiError}</Typography>
        }

        if (isFetchingImgs) {
            return <LoadingSpinner isLoading={isFetchingImgs} />
        }

        return <GeneratedImageList generatedImages={generatedImages} generatedImagesFormat={generatedImagesFormat} promptText={promptText} />
    }


    return (
        <div className={classes.root}>
            <div className={classes.title}>
                <Typography variant="h3">
                    DALL-E Playground <span role="img" aria-label="sparks-emoji">✨</span>
                </Typography>
            </div>
            <div>
                <p>Connected: { '' + isSocketConnected + ' (' + generateComplete + '): ' + socketIds }</p>
            </div>

            {!validBackendUrl && <div>
                <Typography variant="body1" color="textSecondary">
                    Put your DALL-E backend URL to start
                </Typography>
            </div>}

            <div className={classes.playgroundSection}>
                <div className={classes.settingsSection}>
                    <Card className={classes.searchQueryCard}>
                        <CardContent>
                            <BackendUrlInput setBackendValidUrl={setBackendUrl}
                                isValidBackendEndpoint={isValidBackendEndpoint}
                                setIsValidBackendEndpoint={setIsValidBackendEndpoint}
                                setIsCheckingBackendEndpoint={setIsCheckingBackendEndpoint}
                                isCheckingBackendEndpoint={isCheckingBackendEndpoint}
                                disabled={isFetchingImgs} />

                            <TextPromptInput enterPressedCallback={enterPressedCallback} promptText={promptText} setPromptText={setPromptText}
                                disabled={isFetchingImgs || !validBackendUrl} />

                            <NotificationCheckbox isNotificationOn={notificationsOn} setNotifications={setNotificationsOn}/>

                            <FormControl className={classes.imagesPerQueryControl}
                                variant="outlined">
                                <InputLabel id="images-per-query-label">
                                    Images to generate
                                </InputLabel>
                                <Select labelId="images-per-query-label"
                                    label="Images per text prompt" value={imagesPerQuery}
                                    disabled={isFetchingImgs}
                                    onChange={(event) => setImagesPerQuery(event.target.value)}>
                                    {Array.from(Array(imagesPerQueryOptions).keys()).map((num) => {
                                        return <MenuItem key={num + 1} value={num + 1}>
                                            {num + 1}
                                        </MenuItem>
                                    })}
                                </Select>
                                <FormHelperText>More images = More time to generate</FormHelperText>
                            </FormControl>
                        </CardContent>
                    </Card>
                    {queryTime !== 0 && <Typography variant="body2" color="textSecondary">
                        Generation execution time: {queryTime} sec
                    </Typography>}
                </div>
                
                {(generatedImages.length > 0 || apiError || isFetchingImgs) &&
                    <div className={classes.gallery}>
                        {getGalleryContent()}
                    </div>
                }
            </div>
        </div>
    )
}

export default withStyles(useStyles)(App);
