package com.mycoder.rocketchat.data.local

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.mycoder.rocketchat.data.model.Attachment
import com.mycoder.rocketchat.data.model.Mention
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.data.model.Room
import java.util.Date

/**
 * Room database type converters for complex types
 */
class Converters {
    private val gson = Gson()

    @TypeConverter
    fun fromTimestamp(value: Long?): Date? {
        return value?.let { Date(it) }
    }

    @TypeConverter
    fun dateToTimestamp(date: Date?): Long? {
        return date?.time
    }

    @TypeConverter
    fun fromStringList(value: String?): List<String> {
        if (value == null) return emptyList()
        val listType = object : TypeToken<List<String>>() {}.type
        return gson.fromJson(value, listType)
    }

    @TypeConverter
    fun stringListToString(list: List<String>?): String {
        return gson.toJson(list ?: emptyList())
    }

    @TypeConverter
    fun fromAttachmentList(value: String?): List<Attachment>? {
        if (value == null) return null
        val listType = object : TypeToken<List<Attachment>>() {}.type
        return gson.fromJson(value, listType)
    }

    @TypeConverter
    fun attachmentListToString(list: List<Attachment>?): String? {
        return list?.let { gson.toJson(it) }
    }

    @TypeConverter
    fun fromMentionList(value: String?): List<Mention>? {
        if (value == null) return null
        val listType = object : TypeToken<List<Mention>>() {}.type
        return gson.fromJson(value, listType)
    }

    @TypeConverter
    fun mentionListToString(list: List<Mention>?): String? {
        return list?.let { gson.toJson(it) }
    }

    @TypeConverter
    fun fromRoomType(value: String?): Room.RoomType? {
        return value?.let { Room.RoomType.valueOf(it) }
    }

    @TypeConverter
    fun roomTypeToString(type: Room.RoomType?): String? {
        return type?.name
    }

    @TypeConverter
    fun fromSendingStatus(value: String?): Message.SendingStatus? {
        return value?.let { Message.SendingStatus.valueOf(it) }
    }

    @TypeConverter
    fun sendingStatusToString(status: Message.SendingStatus?): String? {
        return status?.name
    }
}
