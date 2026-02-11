---@diagnostic disable: lowercase-global
---@diagnostic disable: undefined-global
-- variables from hyperspace lua api
Hyperspace = Hyperspace
script = script
log = log
Defines = Defines
---@diagnostic enable: undefined-global
---@diagnostic enable: lowercase-global

-- create global method table because apparently that's necessary
Communication = {}

function OnLoad()
    -- initialize vector related variables
    ClientToMod_vector = Hyperspace.vector_int(VectorSize)
    ClientToMod_readIndex = -1

    ModToClient_vector = Hyperspace.vector_int(VectorSize)
    ModToClient_freeSpace = VectorSize - VectorMetaDataSize
    ModToClient_queue = {}
    ModToClient_writeIndex = -1
    ModToClient_readIndex = -1

    ClientToMod_vector[0] = -1  -- lastWriteIndex clientToMod_vector
    ClientToMod_vector[1] = -1  -- lastReadIndex modToClient_vector
    ModToClient_vector[0] = -1  -- lastWriteIndex modToClient_vector
    ModToClient_vector[1] = -1  -- lastReadIndex clientToMod_vector

    Communication.Log("clientToMod Vector - " .. tostring(ClientToMod_vector))
    Communication.Log("modToClient Vector - " .. tostring(ModToClient_vector))

    Communication.Log("Communication module loaded successfully")
end

function Communication.HandleMessage(id, msg)
    if(id <= ClientToMod_readIndex)then
        return -- message has already been processed
    end
    Communication.Log("Recieved Message: "..id.."|"..msg)
    ClientToMod_readIndex = id -- update readIndex (assumes ascending order handling)
    UpdateReadIndex(ModToClient_vector, ClientToMod_readIndex)
end

-- communication methods
function Communication.CheckMessages()
    local messages = Communication.SplitMessages(ClientToMod_vector)
    for _, msg in ipairs(messages) do
        local str = Communication.Decode(msg.data)
        Communication.HandleMessage(msg.id, str)
    end
end
function Communication.SendMessage(message)
    if Communication.AppendMessage(message) then
        -- if the message was sent successfully
    else
        Communication.Log("Message queued: " .. message)
    end
    -- place to add aditional sending logic such as queue handling
end
function Communication.RemoveOldMessages()
    if ClientToMod_vector[1] > ModToClient_readIndex then -- if the readIndex increased
        for i = ModToClient_readIndex + 1, ClientToMod_vector[1] do
            Communication.RemoveMessage(ModToClient_vector, i) -- remove all indexes between
        end
        ModToClient_readIndex = ClientToMod_vector[1] -- update the readIndex
    end
end
-- helper functions
function Communication.Log(msg)
    log(Prefix .. msg)
end

function Communication.Encode(str)
    local result = {}
    for i = 1, #str do
        table.insert(result, string.byte(str, i))
    end
    return result
end
function Communication.Decode(data)
    local chars = {}
    for _, v in ipairs(data) do
        if v == 0 then break end -- stop at null characters
        table.insert(chars, string.char(v))
    end
    return table.concat(chars)
end

-- clears all message data from the vector
function Communication.ClearMessages(vec)
    for i = VectorMetaDataSize, vec:size() - 1 do
        vec[i] = 0
    end
end
-- Writes all messages back-to-back into the vector
function Communication.WriteMessages(vec, messages)
    local writeIndex = VectorMetaDataSize
    for _, msg in ipairs(messages) do
        vec[writeIndex] = msg.id
        vec[writeIndex + 1] = #msg.data
        for k, byte in ipairs(msg.data) do
            vec[writeIndex + 1 + k] = byte
        end
        writeIndex = writeIndex + 2 + #msg.data
    end
end

-- generates a message with it's metaData
function Communication.GenerateMessage(message)
    local messageBodyData = Communication.Encode(message) -- flat byte array
    local result = { ModToClient_writeIndex, #messageBodyData }
    for _, byte in ipairs(messageBodyData) do
        table.insert(result, byte)
    end
    return result
end

-- appends a message to the end of the vector
function Communication.AppendMessage(message)
    if ModToClient_freeSpace < #message + MessageMetaDataSize then
        -- if the message is too long queue it, hopefully never happens, might need to store persistently if we need to be extra safe 
        table.insert(ModToClient_queue, message)
        Communication.Log("Added message to the queue (time to actually implement it...)")
        return false
    end

    ModToClient_writeIndex = ModToClient_writeIndex + 1 -- increment write index

    local messageData = Communication.GenerateMessage(message)

    local startIndex = VectorSize - ModToClient_freeSpace

    for offset = 0, #messageData - 1 do
        ModToClient_vector[startIndex + offset] = messageData[offset + 1]
    end

    ModToClient_freeSpace = ModToClient_freeSpace - #messageData

    ModToClient_vector[0] = ModToClient_writeIndex -- update writeIndex in vector

    return true
end

-- reads a vector and splits it into all messages, returns an ordered table of those messages containing {id, data}
function Communication.SplitMessages(vec)
    local messages = {}
    local i = VectorMetaDataSize
    while i < vec:size() do
        local id = vec[i]
        local length = vec[i + 1]
        if id == nil or length == nil or length == 0 then
            break -- no more messages
        end

        local data = {}
        for j = i + 2, i + 2 + length - 1 do
            table.insert(data, vec[j])
        end

        table.insert(messages, {id = id, data = data})
        i = i + 2 + length
    end
    return messages
end

-- Removes one message by ID and rewrites vector
function Communication.RemoveMessage(vec, removeId)
    local allMessages = Communication.SplitMessages(vec)

    -- Filter out the target
    local filtered = {}
    local removed = {}
    for _, msg in ipairs(allMessages) do
        if msg.id ~= removeId then
            table.insert(filtered, msg)
        else
            table.insert(removed, msg)
        end
    end

    for _, msg in ipairs(removed) do
        ModToClient_freeSpace = ModToClient_freeSpace + #msg.data + 2
    end

    -- Rewrite
    Communication.ClearMessages(vec)
    Communication.WriteMessages(vec, filtered)
end

function UpdateReadIndex(vec, readIndex)
    vec[1] = readIndex
end
function UpdateWriteIndex(vec, writeIndex)
    vec[0] = writeIndex
end

-- static variables
Prefix = "[FTLArchipelago] "
VectorSize = 4096
VectorMetaDataSize = 2 -- last written index of that vector, last read index for the opposing vector
MessageMetaDataSize = 2 -- index of the message, length of the message body

-- register functions
script.on_load(OnLoad)

-- return all methods included in Communication table
return Communication