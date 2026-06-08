local json = GLOBAL.json
local TheSim = GLOBAL.TheSim
local math = GLOBAL.math
local string = GLOBAL.string
local table = GLOBAL.table
local ipairs = GLOBAL.ipairs
local pairs = GLOBAL.pairs
local type = GLOBAL.type
local tostring = GLOBAL.tostring
local tonumber = GLOBAL.tonumber
local pcall = GLOBAL.pcall
local print = GLOBAL.print
local Vector3 = GLOBAL.Vector3

local REQUEST_TIMEOUT = 5
local DEFAULT_NEAR_PLAYER_RADIUS = 20

local function Config(name, default)
    local value = GetModConfigData(name)
    if value == nil then
        return default
    end
    return value
end

local function NormalizeOption(value, default, options)
    value = tonumber(value)
    if value ~= nil then
        for _, option in ipairs(options) do
            if value == option then
                return value
            end
        end
    end
    return default
end

local ENABLE_LOGS = Config("enable_logs", false)
local PROXY_URL = Config("proxy_url", "http://127.0.0.1:8765/say")
local MIN_INTERVAL = NormalizeOption(Config("min_interval_seconds", 20), 20, { 20, 40, 60 })
local MAX_INTERVAL = math.max(MIN_INTERVAL, NormalizeOption(Config("max_interval_seconds", 40), 40, { 40, 60, 80 }))
local TALKER_FONT_SIZE = NormalizeOption(Config("talker_font_size", 24), 24, { 16, 20, 24, 28, 32, 36, 40 })
local GLOBAL_TALK_COOLDOWN = 1

local GROUP_ENABLED =
{
    intelligent = Config("npc_group_intelligent", true),
    animals = Config("npc_group_animals", true),
    monsters = Config("npc_group_monsters", true),
    ocean = Config("npc_group_ocean", true),
}

local PROFILE_DATA =
{
    intelligent =
    {
        group = "intelligent",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -420, 0) or nil,
        fallback =
        {
            "刚才多了一个陌生影子。",
            "有人正在学我说话呀。",
            "门外脚步一直停在原地。",
            "别回头，它已经认人。",
        },
    },
    animal =
    {
        group = "animals",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -240, 0) or nil,
        fallback =
        {
            "洞口刚才自己慢慢合上。",
            "草里有东西同我呼吸。",
            "我的影子慢了整一步。",
            "它闻起来像明天的土。",
        },
    },
    bird =
    {
        group = "animals",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -180, 0) or nil,
        fallback =
        {
            "树梢忽然少了一阵风。",
            "羽毛下面有谁在数数。",
            "地上的影子已经先飞走。",
            "天上的眼睛一直没眨。",
        },
    },
    insect =
    {
        group = "animals",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -160, 0) or nil,
        fallback =
        {
            "花粉里面藏着低语声。",
            "翅膀听见地下轻轻敲门。",
            "甜味从空壳里面出来。",
            "草尖正在数我的细腿。",
        },
    },
    monster =
    {
        group = "monsters",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -300, 0) or nil,
        fallback =
        {
            "黑夜刚才叫了我的名。",
            "影子比牙齿更早饿了。",
            "它躲在我的眼睛后面。",
            "空地中间多了一口呼吸。",
        },
    },
    spider =
    {
        group = "monsters",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -220, 0) or nil,
        fallback =
        {
            "网里吊着明天的影子。",
            "有东西正在学会抖网。",
            "巢外脚印自己走回来。",
            "丝线上挂着细小低语。",
        },
    },
    hound =
    {
        group = "monsters",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -280, 0) or nil,
        fallback =
        {
            "脚印闻起来没有主人。",
            "远处叫声正在装成我。",
            "牙缝里面吹出旧名字。",
            "猎物的影子先跑过来。",
        },
    },
    cave_monster =
    {
        group = "monsters",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -260, 0) or nil,
        fallback =
        {
            "洞壁正在慢慢学呼吸。",
            "回声比声音更先回来。",
            "石头下面有人轻轻笑。",
            "黑暗里面多了一盏眼。",
        },
    },
    clockwork =
    {
        group = "monsters",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -320, 0) or nil,
        fallback =
        {
            "齿轮里面卡着旧心跳。",
            "巡逻路线多出空白一圈。",
            "错误目标正在自己靠近。",
            "停机以后仍有人转动。",
        },
    },
    ocean =
    {
        group = "ocean",
        ensure_talker = true,
        force_say = true,
        no_talk_anim = true,
        talker_offset = Vector3 ~= nil and Vector3(0, -260, 0) or nil,
        fallback =
        {
            "潮水退后留下湿脚印。",
            "泡泡里面有人在眨眼。",
            "水下影子比小船还长。",
            "浪声正在学会人的话。",
        },
    },
}

local PREFAB_TALK =
{
    { prefab = "pigman", profile = "intelligent" },
    { prefab = "pigguard", profile = "intelligent" },
    { prefab = "bunnyman", profile = "intelligent" },
    { prefab = "merm", profile = "intelligent" },
    { prefab = "mermguard", profile = "intelligent" },
    { prefab = "walrus", profile = "intelligent" },
    { prefab = "little_walrus", profile = "intelligent" },
    { prefab = "rocky", profile = "intelligent" },

    { prefab = "rabbit", profile = "animal" },
    { prefab = "mole", profile = "animal" },
    { prefab = "catcoon", profile = "animal" },
    { prefab = "beefalo", profile = "animal" },
    { prefab = "babybeefalo", profile = "animal" },
    { prefab = "koalefant_summer", profile = "animal" },
    { prefab = "koalefant_winter", profile = "animal" },
    { prefab = "lightninggoat", profile = "animal" },
    { prefab = "grassgekko", profile = "animal" },
    { prefab = "perd", profile = "animal" },
    { prefab = "tallbird", profile = "animal" },
    { prefab = "smallbird", profile = "animal" },
    { prefab = "teenbird", profile = "animal" },
    { prefab = "penguin", profile = "animal" },
    { prefab = "butterfly", profile = "insect" },
    { prefab = "lightflier", profile = "insect" },
    { prefab = "lightcrab", profile = "animal" },
    { prefab = "crow", profile = "bird" },
    { prefab = "robin", profile = "bird" },
    { prefab = "robin_winter", profile = "bird" },
    { prefab = "canary", profile = "bird" },
    { prefab = "puffin", profile = "bird" },

    { prefab = "spider", profile = "spider" },
    { prefab = "spider_warrior", profile = "spider" },
    { prefab = "spider_dropper", profile = "spider" },
    { prefab = "spider_hider", profile = "spider" },
    { prefab = "spider_spitter", profile = "spider" },
    { prefab = "spider_water", profile = "spider" },
    { prefab = "hound", profile = "hound" },
    { prefab = "firehound", profile = "hound" },
    { prefab = "icehound", profile = "hound" },
    { prefab = "frog", profile = "monster" },
    { prefab = "mosquito", profile = "insect", group = "monsters" },
    { prefab = "bee", profile = "insect", group = "monsters" },
    { prefab = "killerbee", profile = "insect", group = "monsters" },
    { prefab = "bat", profile = "cave_monster" },
    { prefab = "ruins_bat", profile = "cave_monster" },
    { prefab = "molebat", profile = "cave_monster" },
    { prefab = "slurper", profile = "cave_monster" },
    { prefab = "slurtle", profile = "cave_monster" },
    { prefab = "snurtle", profile = "cave_monster" },
    { prefab = "worm", profile = "cave_monster" },
    { prefab = "tentacle", profile = "cave_monster" },
    { prefab = "birchnutdrake", profile = "monster" },
    { prefab = "krampus", profile = "monster" },
    { prefab = "monkey", profile = "animal", group = "monsters" },
    { prefab = "knight", profile = "clockwork" },
    { prefab = "bishop", profile = "clockwork" },
    { prefab = "rook", profile = "clockwork" },
    { prefab = "knight_nightmare", profile = "clockwork" },
    { prefab = "bishop_nightmare", profile = "clockwork" },
    { prefab = "rook_nightmare", profile = "clockwork" },

    { prefab = "cookiecutter", profile = "ocean" },
    { prefab = "squid", profile = "ocean" },
    { prefab = "gnarwail", profile = "ocean" },
    { prefab = "shark", profile = "ocean" },
    { prefab = "wobster_sheller", profile = "ocean" },
    { prefab = "wobster_sheller_land", profile = "ocean" },
    { prefab = "wobster_moonglass", profile = "ocean" },
    { prefab = "wobster_moonglass_land", profile = "ocean" },
}

local function Log(message)
    if ENABLE_LOGS then
        print("[AI NPC Talk] " .. tostring(message))
    end
end

Log("effective interval " .. tostring(MIN_INTERVAL) .. "-" .. tostring(MAX_INTERVAL) .. " seconds")

local last_global_talk_at = -GLOBAL_TALK_COOLDOWN

local function EntityLabel(inst)
    if inst == nil then
        return "nil"
    end

    return tostring(inst.prefab or "unknown") .. "#" .. tostring(inst.GUID or "unknown")
end

local function NpcLog(npc_id, inst, message)
    Log(tostring(npc_id) .. " " .. EntityLabel(inst) .. ": " .. tostring(message))
end

local function GetNow()
    return GLOBAL.GetTime ~= nil and GLOBAL.GetTime() or 0
end

local function TryConsumeGlobalTalkSlot(npc_id, inst)
    local now = GetNow()
    if now - last_global_talk_at < GLOBAL_TALK_COOLDOWN then
        NpcLog(npc_id, inst, "skip request: global talk cooldown")
        return false
    end

    last_global_talk_at = now
    return true
end

local function IsMasterSim()
    return GLOBAL.TheWorld ~= nil and GLOBAL.TheWorld.ismastersim
end

local function IsValidInst(inst)
    return inst ~= nil and inst:IsValid() and not inst:HasTag("INLIMBO")
end

local function InvalidReason(inst)
    if inst == nil then
        return "inst is nil"
    end
    if not inst:IsValid() then
        return "inst is invalid"
    end
    if inst:HasTag("INLIMBO") then
        return "inst is in limbo"
    end
    return nil
end

local function HasNearbyPlayer(inst, radius)
    if GLOBAL.AllPlayers == nil then
        return true
    end

    radius = radius or DEFAULT_NEAR_PLAYER_RADIUS
    local radius_sq = radius * radius
    for _, player in ipairs(GLOBAL.AllPlayers) do
        if player ~= nil
            and player:IsValid()
            and not player:HasTag("playerghost")
            and player:GetDistanceSqToInst(inst) <= radius_sq then
            return true
        end
    end

    return false
end

local function GetWorldState(name, default)
    if GLOBAL.TheWorld ~= nil and GLOBAL.TheWorld.state ~= nil and GLOBAL.TheWorld.state[name] ~= nil then
        return tostring(GLOBAL.TheWorld.state[name])
    end
    return default
end

local function UrlEncode(value)
    value = tostring(value or "")
    value = string.gsub(value, "\n", "\r\n")
    value = string.gsub(value, "([^%w%-_%.~])", function(char)
        return string.format("%%%02X", string.byte(char))
    end)
    return value
end

local function AppendQuery(url, params)
    local sep = string.find(url, "?", 1, true) ~= nil and "&" or "?"
    local parts = {}

    for key, value in pairs(params) do
        table.insert(parts, UrlEncode(key) .. "=" .. UrlEncode(value))
    end

    return url .. sep .. table.concat(parts, "&")
end

local function CleanText(text)
    if type(text) ~= "string" then
        return nil
    end

    text = string.gsub(text, "[\r\n]", " ")
    text = string.gsub(text, "^%s+", "")
    text = string.gsub(text, "%s+$", "")
    text = string.gsub(text, "^['\"]+", "")
    text = string.gsub(text, "['\"]+$", "")

    if text == "" then
        return nil
    end

    return text
end

local function ExtractText(result)
    if type(result) ~= "string" or result == "" then
        return nil
    end

    if json ~= nil and json.decode ~= nil then
        local ok, data = pcall(json.decode, result)
        if ok and type(data) == "table" then
            local text = CleanText(data.text)
            if text ~= nil then
                return text
            end
        end
    end

    return CleanText(string.match(result, '"text"%s*:%s*"([^"]*)"'))
end

local function SayLine(inst, data, text, npc_id, source)
    local invalid_reason = InvalidReason(inst)
    if invalid_reason ~= nil then
        NpcLog(npc_id, inst, "skip say " .. tostring(source) .. ": " .. invalid_reason)
        return false
    end

    if inst.components == nil or inst.components.talker == nil then
        NpcLog(npc_id, inst, "skip say " .. tostring(source) .. ": no talker component")
        return false
    end

    inst.components.talker:Say(text, nil, data.no_talk_anim == true, data.force_say == true)
    NpcLog(npc_id, inst, "say " .. tostring(source))
    return true
end

local function SayFallback(inst, data, npc_id)
    local fallback = data.fallback
    return SayLine(inst, data, fallback[math.random(#fallback)], npc_id, "fallback")
end

local function SayText(inst, data, text, npc_id)
    return SayLine(inst, data, text, npc_id, "text")
end

local function EnsureTalker(inst, data)
    if not data.ensure_talker then
        return
    end

    if inst.components == nil then
        NpcLog("talker", inst, "cannot add talker: no components table")
        return
    end

    local talker = inst.components.talker
    if talker == nil then
        if inst.AddComponent == nil then
            NpcLog("talker", inst, "cannot add talker: AddComponent missing")
            return
        end

        inst:AddComponent("talker")
        talker = inst.components.talker
        NpcLog("talker", inst, "talker added")
    end

    if talker ~= nil then
        talker.fontsize = TALKER_FONT_SIZE
        if GLOBAL.TALKINGFONT ~= nil then
            talker.font = GLOBAL.TALKINGFONT
        end
        if data.talker_offset ~= nil then
            talker.offset = data.talker_offset
        end
    end
end

local function BuildRequestUrl(inst, npc_id)
    local params =
    {
        npc = npc_id,
        prefab = inst ~= nil and inst.prefab ~= nil and tostring(inst.prefab) or "unknown",
        entity = inst ~= nil and inst.GUID ~= nil and tostring(inst.GUID) or "unknown",
        event = "idle",
        season = GetWorldState("season", "unknown"),
        phase = GetWorldState("phase", "unknown"),
        day = GetWorldState("cycles", "0"),
        cave = GLOBAL.TheWorld ~= nil and GLOBAL.TheWorld:HasTag("cave") and "1" or "0",
    }

    return AppendQuery(PROXY_URL, params)
end

local function RequestLine(inst, npc_id, data)
    local invalid_reason = InvalidReason(inst)
    if invalid_reason ~= nil then
        NpcLog(npc_id, inst, "skip request: " .. invalid_reason)
        return
    end

    if inst.ai_npc_talk_pending then
        NpcLog(npc_id, inst, "skip request: request already pending")
        return
    end

    if not HasNearbyPlayer(inst, data.near_player_radius) then
        NpcLog(npc_id, inst, "skip request: no nearby player within " .. tostring(data.near_player_radius or DEFAULT_NEAR_PLAYER_RADIUS))
        return
    end

    if not TryConsumeGlobalTalkSlot(npc_id, inst) then
        return
    end

    if TheSim == nil or TheSim.QueryServer == nil then
        NpcLog(npc_id, inst, "QueryServer unavailable; using fallback")
        SayFallback(inst, data, npc_id)
        return
    end

    inst.ai_npc_talk_pending = true
    inst.ai_npc_talk_request_id = (inst.ai_npc_talk_request_id or 0) + 1

    local request_id = inst.ai_npc_talk_request_id
    local url = BuildRequestUrl(inst, npc_id)
    NpcLog(npc_id, inst, "requesting proxy")

    inst:DoTaskInTime(REQUEST_TIMEOUT + 1, function()
        if IsValidInst(inst)
            and inst.ai_npc_talk_pending
            and inst.ai_npc_talk_request_id == request_id then
            inst.ai_npc_talk_pending = false
            NpcLog(npc_id, inst, "proxy timeout")
            SayFallback(inst, data, npc_id)
        end
    end)

    local ok, err = pcall(function()
        TheSim:QueryServer(url, function(result, is_successful, http_code)
            if not IsValidInst(inst)
                or inst.ai_npc_talk_request_id ~= request_id
                or not inst.ai_npc_talk_pending then
                return
            end

            inst.ai_npc_talk_pending = false

            if is_successful and http_code == 200 then
                local text = ExtractText(result)
                if text ~= nil then
                    NpcLog(npc_id, inst, "proxy success")
                    SayText(inst, data, text, npc_id)
                    return
                end
            end

            NpcLog(npc_id, inst, "proxy failed: " .. tostring(http_code))
            SayFallback(inst, data, npc_id)
        end, "GET", nil, REQUEST_TIMEOUT)
    end)

    if not ok then
        inst.ai_npc_talk_pending = false
        NpcLog(npc_id, inst, "QueryServer error: " .. tostring(err))
        SayFallback(inst, data, npc_id)
    end
end

local function ScheduleNext(inst, npc_id, data, min_delay, max_delay)
    local invalid_reason = InvalidReason(inst)
    if invalid_reason ~= nil then
        NpcLog(npc_id, inst, "skip schedule: " .. invalid_reason)
        return
    end

    local min_interval = min_delay or data.min_interval or MIN_INTERVAL
    local max_interval = math.max(min_interval, max_delay or data.max_interval or MAX_INTERVAL)
    local delay = math.random(min_interval, max_interval)
    NpcLog(npc_id, inst, "scheduled in " .. tostring(delay) .. " seconds")
    inst.ai_npc_talk_task = inst:DoTaskInTime(delay, function()
        RequestLine(inst, npc_id, data)
        ScheduleNext(inst, npc_id, data)
    end)
end

local function IsPrefabTalkEnabled(def, data)
    local group = def.group or data.group
    if group ~= nil and GROUP_ENABLED[group] == false then
        return false
    end

    return true
end

local function AttachPrefabTalk(def)
    local data = PROFILE_DATA[def.profile]
    if data == nil or not IsPrefabTalkEnabled(def, data) then
        return
    end

    AddPrefabPostInit(def.prefab, function(inst)
        EnsureTalker(inst, data)

        if not IsMasterSim() then
            return
        end

        NpcLog(def.profile, inst, "attached")

        ScheduleNext(inst, def.profile, data)
    end)
end

for _, def in ipairs(PREFAB_TALK) do
    AttachPrefabTalk(def)
end
