// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ChainProof Model Registry
/// @notice Stores tamper-evident AI model registrations on-chain.
/// @dev Only hashes/Merkle roots are stored on-chain, not private datasets or model files.
contract ModelRegistry {
    struct ModelRecord {
        string recordId;
        string modelName;
        string version;
        string datasetMerkleRoot;
        string modelHash;
        string configHash;
        address registeredBy;
        uint256 timestamp;
    }

    mapping(string => ModelRecord) private records;
    mapping(string => bool) private recordExists;
    mapping(string => string[]) private modelHistory;
    string[] private allRecordIds;

    event ModelRegistered(
        string indexed recordId,
        string indexed modelName,
        string version,
        string datasetMerkleRoot,
        string modelHash,
        string configHash,
        address indexed registeredBy,
        uint256 timestamp
    );

    /// @notice Registers a new immutable model version.
    /// @dev A recordId can only be used once. Use a new recordId for every model version.
    function registerModel(
        string memory recordId,
        string memory modelName,
        string memory version,
        string memory datasetMerkleRoot,
        string memory modelHash,
        string memory configHash
    ) public {
        require(bytes(recordId).length > 0, "recordId required");
        require(bytes(modelName).length > 0, "modelName required");
        require(bytes(version).length > 0, "version required");
        require(bytes(datasetMerkleRoot).length > 0, "datasetMerkleRoot required");
        require(bytes(modelHash).length > 0, "modelHash required");
        require(bytes(configHash).length > 0, "configHash required");
        require(!recordExists[recordId], "record already exists");

        records[recordId] = ModelRecord({
            recordId: recordId,
            modelName: modelName,
            version: version,
            datasetMerkleRoot: datasetMerkleRoot,
            modelHash: modelHash,
            configHash: configHash,
            registeredBy: msg.sender,
            timestamp: block.timestamp
        });

        recordExists[recordId] = true;
        modelHistory[modelName].push(recordId);
        allRecordIds.push(recordId);

        emit ModelRegistered(
            recordId,
            modelName,
            version,
            datasetMerkleRoot,
            modelHash,
            configHash,
            msg.sender,
            block.timestamp
        );
    }

    /// @notice Checks whether a record ID exists.
    function exists(string memory recordId) public view returns (bool) {
        return recordExists[recordId];
    }

    /// @notice Reads one model record by record ID.
    function getModel(string memory recordId) public view returns (ModelRecord memory) {
        require(recordExists[recordId], "record not found");
        return records[recordId];
    }

    /// @notice Returns all record IDs registered for one model name.
    function getModelHistory(string memory modelName) public view returns (string[] memory) {
        return modelHistory[modelName];
    }

    /// @notice Returns the number of versions registered for one model name.
    function getVersionCount(string memory modelName) public view returns (uint256) {
        return modelHistory[modelName].length;
    }

    /// @notice Returns the newest registration for one model name.
    function getLatestModel(string memory modelName) public view returns (ModelRecord memory) {
        uint256 length = modelHistory[modelName].length;
        require(length > 0, "model not found");
        string memory latestRecordId = modelHistory[modelName][length - 1];
        return records[latestRecordId];
    }

    /// @notice Returns all registered record IDs. Useful for frontend registry pages.
    function getAllRecordIds() public view returns (string[] memory) {
        return allRecordIds;
    }

    /// @notice Returns the total number of registrations.
    function getTotalRecords() public view returns (uint256) {
        return allRecordIds.length;
    }
}
