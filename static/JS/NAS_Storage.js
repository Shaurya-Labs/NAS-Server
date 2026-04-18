// Create folder button functionality
const createFolderBtn = document.getElementById("create_folder_btn");
const closeNewFolderModal = document.getElementById("close_new_folder_modal");
const cancel = document.getElementById("close_new_folder_modal")
const folderNameModal = document.getElementById("folder_name_modal");

createFolderBtn.addEventListener("click", () => folderNameModal.style.display = "flex");
cancel.addEventListener("click", () => {folderNameModal.style.display = "none"});

// Selecting and deselecting files
const selectedFiles = [];
const filesListContainer = document.querySelector("#files_list_container, #img_or_vid_container");

function selectFilesHandler(event) {
    const fileElement = event.target.closest(".file_btn, .img_btn, .media_btn");

    if (!fileElement) {
        console.log("does not include any class")
        return
    }

    console.log("contains class")

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
const csrfToken = document.querySelector("meta[name='csrf_token']").content

async function postSelectedFiles(selectedFiles) {
    const response = await fetch("/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(selectedFiles)
    })

    console.log(await response.text())
}

async function deleteBtnHandler(selectedFiles) {
    if (selectedFiles.length !== 0) {
        await postSelectedFiles(selectedFiles);
        selectedFiles.length = 0;
        window.location.reload();
    }
}

deleteBtn.addEventListener("click", () => deleteBtnHandler(selectedFiles))

// Downloading files

/**
 * This helper function sends a HTML form containing selected files's nas_file_path to the backend server.
 */
function downloadBtnHandler(selectedFiles) {
    console.log("download button pressed");

    const downloadFileForm = document.createElement("form");
    const downloadFileFormCsrfToken = document.createElement("input");

    downloadFileForm.hidden = true;
    downloadFileForm.action = "/download";
    downloadFileForm.method = "POST";

    downloadFileFormCsrfToken.type = "hidden";
    downloadFileFormCsrfToken.name = "csrf_token";
    downloadFileFormCsrfToken.value = csrfToken;

    for (filename of selectedFiles) {
        const downloadFileFormFileName = document.createElement("input");

        downloadFileFormFileName.type = "hidden";
        downloadFileFormFileName.name = "filename";
        downloadFileFormFileName.value = filename;

        downloadFileForm.appendChild(downloadFileFormFileName);
    }

    downloadFileForm.appendChild(downloadFileFormCsrfToken);
    document.body.appendChild(downloadFileForm);

    console.log("Submitting the form");

    downloadFileForm.submit();
}

const downloadBtn = document.getElementById("download_btn");
downloadBtn.addEventListener("click", () => downloadBtnHandler(selectedFiles));