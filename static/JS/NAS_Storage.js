const csrfToken = document.querySelector("meta[name='csrf_token']").content;
const currentNasFolderPath = document.querySelector("meta[name='current_nas_folder_path']").content;

// Create folder button functionality
const createFolderBtn = document.getElementById("create_folder_btn");
const closeNewFolderModal = document.getElementById("close_new_folder_modal");
const cancel = document.getElementById("close_new_folder_modal");
const folderNameModal = document.getElementById("folder_name_modal");

createFolderBtn.addEventListener("click", () => folderNameModal.style.display = "flex");
cancel.addEventListener("click", () => {folderNameModal.style.display = "none"});

// Selecting and deselecting files
const selectedFiles = [];       // array of nas file paths of selected files
const filesListContainer = document.querySelector("#files_list_container, #img_or_vid_container");

function selectFilesHandler(event) {
    const fileElement = event.target.closest(".file_btn, .image_btn, .media_btn");

    if (!fileElement) {
        return
    }

    const nasFilePath = fileElement.dataset.nasFilePath
    const fileBtnToSelect = document.querySelector(`[data-nas-file-path="${nasFilePath}"]`);
    if (selectedFiles.includes(nasFilePath)) {
        fileBtnToSelect.classList.remove("file_selected_btn")
        selectedFiles.splice(selectedFiles.indexOf(nasFilePath), 1)
    }
    else {
        fileBtnToSelect.classList.add("file_selected_btn");
        selectedFiles.push(nasFilePath);
    }
}
filesListContainer.addEventListener("click", (event) => selectFilesHandler(event));

// Deleting files
const deleteBtn = document.getElementById("delete_btn");

async function postSelectedFiles(selectedFiles) {
    const response = await fetch("/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(selectedFiles)
    })
}

async function deleteBtnHandler(selectedFiles) {
    if (selectedFiles.length !== 0) {
        await postSelectedFiles(selectedFiles);
        selectedFiles.length = 0;
        window.location.reload();
    }
}
deleteBtn.addEventListener("click", () => {
    if (selectedFiles.length >= 1) {
        deleteBtnHandler(selectedFiles)
    }
});

// Downloading files
/**
 * This helper function sends a HTML form containing selected files's nas_file_path to the backend server.
 */
function downloadBtnHandler(selectedFiles) {
    const downloadFileForm = document.createElement("form");
    const downloadFileFormCsrfToken = document.createElement("input");

    downloadFileForm.hidden = true;
    downloadFileForm.action = "/download";
    downloadFileForm.method = "POST";

    downloadFileFormCsrfToken.type = "hidden";
    downloadFileFormCsrfToken.name = "csrf_token";
    downloadFileFormCsrfToken.value = csrfToken;

    for (const nasFilePath of selectedFiles) {
        const downloadFileFormFileName = document.createElement("input");

        downloadFileFormFileName.type = "hidden";
        downloadFileFormFileName.name = "nasFilePath";
        downloadFileFormFileName.value = nasFilePath;

        downloadFileForm.appendChild(downloadFileFormFileName);
    }

    downloadFileForm.appendChild(downloadFileFormCsrfToken);
    document.body.appendChild(downloadFileForm);

    downloadFileForm.submit();
    downloadFileForm.remove();
}
const downloadBtn = document.getElementById("download_btn");

downloadBtn.addEventListener("click", () => {
    if (selectedFiles.length >= 1) {
        downloadBtnHandler(selectedFiles);
    }
});

// Uploading files
const filesToUpload = document.getElementById("files-to-upload");
const filesUploadBtn = document.getElementById("files-upload-btn");
const filesUploadProgressBar = document.getElementById("files-upload-progress-bar");

filesUploadBtn.addEventListener("click", () => {

    if (filesToUpload.files.length === 0) {
        return;
    }

    const payload = new FormData();
    payload.append("csrf_token", csrfToken);
    payload.append("current_nas_folder_path", currentNasFolderPath);

    for (const file of filesToUpload.files) {
        payload.append("files", file);      // Adding files pointers to payload object
    }

    const request = new XMLHttpRequest();
    request.open("POST", "/upload");

    let lastLoaded = 0;
    let lastTime = performance.now();
    const uploadSpeedmoter = document.getElementById("upload-speedometer");
    request.upload.addEventListener("progress", (event) => {
        const currentTime = performance.now();

        const bytesSent = event.loaded - lastLoaded;
        const timePassedMs = currentTime - lastTime;

        if (timePassedMs != 0) {
            const speedMBps = (bytesSent / timePassedMs) / 1024;
            uploadSpeedmoter.innerHTML = `${speedMBps} MB/s`
        }

        lastLoaded = event.loaded;
        lastTime = currentTime;

        const percentComplete = (event.loaded / event.total)*100;
        filesUploadProgressBar.setAttribute("value", percentComplete);
        filesUploadProgressBar.nextElementSibling.innerHTML = `${percentComplete}%`;
    });

    request.addEventListener("load", () => {        // If files are saved successfully on server, reload the window
        if (request.status === 200) {
            window.location.reload();
        }
    });

    // Only display progress bar when files are chosen and upload button is clicked
    const filesUploadProgressBarContainer = document.getElementById("files-upload-progress-bar-container");
    filesUploadProgressBarContainer.style.display = "flex";

    request.send(payload);
});

// Viewing chosen file names
function viewChoosenFileNamesHandler() {
    const chosenFileNames = document.getElementById("chosen_file_names");
    chosenFileNames.innerHTML = '';

    for (const file of filesToUpload.files) {
        const span = document.createElement("span");
        span.textContent = file.name;
        chosenFileNames.appendChild(span)
    }
}
const chooseFiles = document.getElementById("choose_files");
chooseFiles.addEventListener("change", viewChoosenFileNamesHandler);

// Image viewer modal
const imgViewerModal = document.getElementById("image_viewer_modal");
const imgBtns = document.querySelectorAll(".image_btn");
const imgDownloadBtn = document.getElementById("image_download_btn");
let currentImgSource = null;

async function imgBtnHandler(imgBtn) {
    const imgContainer = document.getElementById("image_container");
    const img = document.createElement("img");
    currentImgSource = imgBtn.dataset.nasFilePath;
    imgContainer.innerHTML = "";
    
    // Placed before fetching the image, so that the browser doens't lag behind(becasue of loading the image) showing the modal when the user double clicks
    imgViewerModal.style.display = "flex";
    
    // downloading the image from fetch so that the whole image is displayed at once without making it load from top to bottom slowly(which could happen by using img.src tag)
    const response = await fetch(`/media/${currentImgSource}`);
    const url = URL.createObjectURL(await response.blob());
    img.onload = () => URL.revokeObjectURL(url);
    img.src = url;
    imgContainer.appendChild(img);

    const imgNameDiv = document.getElementById("image_name");
    imgNameDiv.innerHTML = currentImgSource.split("/").pop();
}

imgBtns.forEach((imgBtn) => {
    imgBtn.addEventListener("dblclick", () => imgBtnHandler(imgBtn))
});
imgViewerModal.addEventListener("click", (event) => {
    if (event.target.id === "image_container") {
        imgViewerModal.style.display = "none";
    }
});

imgDownloadBtn.addEventListener("click", () => downloadBtnHandler([currentImgSource]));     //downlading the image when download image btn is clicked

// Video player modal
const videoPlayerModal = document.getElementById("video_player_modal");
const videoBtns = document.querySelectorAll(".media_btn");
const videoPlayer = document.getElementById("video_player");
let currentVideoSource = null;

function videoBtnHandler(videoBtn) {
    const video = document.createElement("video");
    currentVideoSource = videoBtn.dataset.nasFilePath;
    videoPlayer.innerHTML = ""

    videoPlayerModal.style.display = "flex";

    video.src = `/media/${currentVideoSource}`;
    video.controls = true;

    videoPlayer.appendChild(video);
    const videoNameDiv = document.getElementById("video_name");
    videoNameDiv.innerHTML = currentVideoSource.split("/").pop();
}

videoBtns.forEach((videoBtn) => {
    videoBtn.addEventListener("dblclick", () => videoBtnHandler(videoBtn))
});

videoPlayerModal.addEventListener("click", (event) => {
    if (event.target.id == "video_player") {
        videoPlayer.innerHTML = ""
        videoPlayerModal.style.display = "none";
    }
});

// Video thumbnail polling
function appendThumbnailHtml(loadingSpanTag, thumbnailUrl) {
    const img = document.createElement("img");
    img.src = thumbnailUrl;

    loadingSpanTag.replaceWith(img);
}

async function pollThumbnailStatus(loadingSpanTag) {
        const thumbnailUrl = loadingSpanTag.dataset.thumbnailUrl;

        // Checking thumbnail status before setting up interval because setIneverval first waits for 2 seconds(inverval time) and then checks thumbnail status, which causes 2 seconds delay after loading webpage.
        const immidiateResponse = await fetch(thumbnailUrl, {method: "HEAD"});
        if (immidiateResponse.status === 200) {
            appendThumbnailHtml(loadingSpanTag, thumbnailUrl);
            return;
        }
        
        const pollIntervalId = setInterval(async () => {
            const response = await fetch(thumbnailUrl, {method: "HEAD"});
            if (response.status === 200) {
                clearInterval(pollIntervalId);
                appendThumbnailHtml(loadingSpanTag, thumbnailUrl);
            }
        }, 2000);
    }

const videoThumbnailLoadingSpans = document.querySelectorAll(".video_thumbnail_loading");
videoThumbnailLoadingSpans.forEach((loadingSpanTag) => {
    pollThumbnailStatus(loadingSpanTag);
});

// File navigation
const preBtn = document.getElementById("previous_btn");
const nextBtn = document.getElementById("next_btn");

function getCurrentPage() {
    let currentPage = new URLSearchParams(window.location.search).get("page");
    if (currentPage === null) {
        currentPage = 1;
    }
    currentPage = parseInt(currentPage)
    return currentPage || 1;        //if currentPage is not an int, then it would return 1
}

if (preBtn && nextBtn) {        // Add event listeners if pre and next buttons are to be displayed on screen
        nextBtn.addEventListener("click", () => {
        const currentPage = getCurrentPage();
        let pageToRedirect;
        if (currentPage <= 0) {
            pageToRedirect = 1;
        }
        else {
            pageToRedirect = currentPage + 1;
        }
        window.location.search = `page=${pageToRedirect}`
    });
    preBtn.addEventListener("click", () => {
        const currentPage = getCurrentPage();
        let pageToRedirect;
        if (currentPage <= 1) {
            pageToRedirect = 1;
        }
        else {
            pageToRedirect = currentPage - 1;
        }
        window.location.search = `page=${pageToRedirect}`
    });
}
